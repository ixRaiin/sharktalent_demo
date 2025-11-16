# Routes.py to Handle Application Routing and Application Re-Direction.

from flask import Blueprint, request, jsonify
from models import db, User, Project, Proposal
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth import role_required

# Create blueprints
project_bp = Blueprint('projects', __name__)
proposal_bp = Blueprint('proposals', __name__)

# Project Routes

# Get all open projects
@project_bp.route('/', methods=['GET'])
@jwt_required()
def get_projects():
    try:
        # Get query parameters for filtering
        status = request.args.get('status', 'open')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Build query
        query = Project.query
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginate results
        projects = query.order_by(Project.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        project_list = []
        for project in projects.items:
            project_list.append({
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'budget': project.budget,
                'skills_required': project.skills_required,
                'status': project.status,
                'client_id': project.client_id,
                'created_at': project.created_at.isoformat(),
                'client_name': f"{project.client.first_name} {project.client.last_name}"
            })
        
        return jsonify({
            'projects': project_list,
            'total': projects.total,
            'pages': projects.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching projects: {str(e)}'}), 500

# Get a single project by ID
@project_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    try:
        project = Project.query.get_or_404(project_id)
        
        return jsonify({
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'budget': project.budget,
            'skills_required': project.skills_required,
            'status': project.status,
            'client_id': project.client_id,
            'created_at': project.created_at.isoformat(),
            'client_name': f"{project.client.first_name} {project.client.last_name}"
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching project: {str(e)}'}), 500

# Create a new project
@project_bp.route('/', methods=['POST'])
@jwt_required()
@role_required('client')
def create_project(client_user):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'budget', 'skills_required']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Create project
        project = Project(
            title=data['title'],
            description=data['description'],
            budget=float(data['budget']),
            skills_required=data['skills_required'],
            client_id=client_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project created successfully',
            'project_id': project.id
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error creating project: {str(e)}'}), 500

# Update a project
@project_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    try:
        current_user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        
        # Check if user owns the project or is admin
        if project.client_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = ['title', 'description', 'budget', 'skills_required', 'status']
        for field in updatable_fields:
            if field in data:
                setattr(project, field, data[field])
        
        db.session.commit()
        
        return jsonify({'message': 'Project updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error updating project: {str(e)}'}), 500

# Delete a project
@project_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    try:
        current_user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        
        # Check if user owns the project or is admin
        if project.client_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({'message': 'Access denied'}), 403
        
        # Delete associated proposals first
        Proposal.query.filter_by(project_id=project_id).delete()
        
        # Delete project
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'message': 'Project deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error deleting project: {str(e)}'}), 500

# Get projects created by current client
@project_bp.route('/my-projects', methods=['GET'])
@jwt_required()
@role_required('client')
def get_my_projects(client_user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        projects = Project.query.filter_by(client_id=client_user.id)\
            .order_by(Project.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        project_list = []
        for project in projects.items:
            # Count proposals for each project
            proposal_count = Proposal.query.filter_by(project_id=project.id).count()
            
            project_list.append({
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'budget': project.budget,
                'skills_required': project.skills_required,
                'status': project.status,
                'created_at': project.created_at.isoformat(),
                'proposal_count': proposal_count
            })
        
        return jsonify({
            'projects': project_list,
            'total': projects.total,
            'pages': projects.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching your projects: {str(e)}'}), 500

# Proposal Routes

# Submit a proposal for a project
@proposal_bp.route('/', methods=['POST'])
@jwt_required()
@role_required('freelancer')
def create_proposal(freelancer_user):
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['project_id', 'cover_letter', 'bid_amount', 'timeline_days']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        project_id = data['project_id']
        
        # Check if project exists and is open
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'message': 'Project not found'}), 404
        
        if project.status != 'open':
            return jsonify({'message': 'Project is not accepting proposals'}), 400
        
        # Check proposal limit (3 per project per freelancer)
        existing_proposals = Proposal.query.filter_by(
            freelancer_id=freelancer_user.id, 
            project_id=project_id
        ).count()
        
        if existing_proposals >= 3:
            return jsonify({'message': 'Proposal limit reached (3 proposals per project)'}), 400
        
        # Create proposal
        proposal = Proposal(
            cover_letter=data['cover_letter'],
            bid_amount=float(data['bid_amount']),
            timeline_days=int(data['timeline_days']),
            freelancer_id=freelancer_user.id,
            project_id=project_id
        )
        
        db.session.add(proposal)
        db.session.commit()
        
        return jsonify({
            'message': 'Proposal submitted successfully',
            'proposal_id': proposal.id
        }), 201
        
    except Exception as e:
        return jsonify({'message': f'Error submitting proposal: {str(e)}'}), 500

# Get proposals for a project (client only)
@proposal_bp.route('/project/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project_proposals(project_id):
    try:
        current_user_id = get_jwt_identity()
        project = Project.query.get_or_404(project_id)
        
        # Check if user owns the project or is admin
        if project.client_id != current_user_id:
            user = User.query.get(current_user_id)
            if user.role != 'admin':
                return jsonify({'message': 'Access denied'}), 403
        
        proposals = Proposal.query.filter_by(project_id=project_id)\
            .order_by(Proposal.submitted_at.desc())\
            .all()
        
        proposal_list = []
        for proposal in proposals:
            proposal_list.append({
                'id': proposal.id,
                'cover_letter': proposal.cover_letter,
                'bid_amount': proposal.bid_amount,
                'timeline_days': proposal.timeline_days,
                'status': proposal.status,
                'submitted_at': proposal.submitted_at.isoformat(),
                'freelancer': {
                    'id': proposal.freelancer.id,
                    'name': f"{proposal.freelancer.first_name} {proposal.freelancer.last_name}",
                    'email': proposal.freelancer.email
                }
            })
        
        return jsonify({'proposals': proposal_list}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching proposals: {str(e)}'}), 500

# Get proposals submitted by current freelancer
@proposal_bp.route('/my-proposals', methods=['GET'])
@jwt_required()
@role_required('freelancer')
def get_my_proposals(freelancer_user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        proposals = Proposal.query.filter_by(freelancer_id=freelancer_user.id)\
            .order_by(Proposal.submitted_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        proposal_list = []
        for proposal in proposals.items:
            proposal_list.append({
                'id': proposal.id,
                'cover_letter': proposal.cover_letter,
                'bid_amount': proposal.bid_amount,
                'timeline_days': proposal.timeline_days,
                'status': proposal.status,
                'submitted_at': proposal.submitted_at.isoformat(),
                'project': {
                    'id': proposal.project.id,
                    'title': proposal.project.title,
                    'budget': proposal.project.budget,
                    'status': proposal.project.status,
                    'client_name': f"{proposal.project.client.first_name} {proposal.project.client.last_name}"
                }
            })
        
        return jsonify({
            'proposals': proposal_list,
            'total': proposals.total,
            'pages': proposals.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching your proposals: {str(e)}'}), 500

# Update proposal status (client only - accept/reject)
@proposal_bp.route('/<int:proposal_id>/status', methods=['PUT'])
@jwt_required()
def update_proposal_status(proposal_id):
    try:
        current_user_id = get_jwt_identity()
        proposal = Proposal.query.get_or_404(proposal_id)
        project = Project.query.get(proposal.project_id)
        
        # Check if user owns the project
        if project.client_id != current_user_id:
            return jsonify({'message': 'Access denied'}), 403
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['accepted', 'rejected']:
            return jsonify({'message': 'Status must be "accepted" or "rejected"'}), 400
        
        # Update proposal status
        proposal.status = new_status
        
        # If accepting a proposal, reject all others for this project
        if new_status == 'accepted':
            Proposal.query.filter(
                Proposal.project_id == project.id,
                Proposal.id != proposal_id
            ).update({'status': 'rejected'})
            
            # Update project status to in_progress
            project.status = 'in_progress'
        
        db.session.commit()
        
        return jsonify({'message': f'Proposal {new_status} successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Error updating proposal status: {str(e)}'}), 500

# Get a single proposal
@proposal_bp.route('/<int:proposal_id>', methods=['GET'])
@jwt_required()
def get_proposal(proposal_id):
    try:
        current_user_id = get_jwt_identity()
        proposal = Proposal.query.get_or_404(proposal_id)
        
        # Check if user has access to this proposal
        user = User.query.get(current_user_id)
        has_access = (
            proposal.freelancer_id == current_user_id or
            proposal.project.client_id == current_user_id or
            user.role == 'admin'
        )
        
        if not has_access:
            return jsonify({'message': 'Access denied'}), 403
        
        return jsonify({
            'id': proposal.id,
            'cover_letter': proposal.cover_letter,
            'bid_amount': proposal.bid_amount,
            'timeline_days': proposal.timeline_days,
            'status': proposal.status,
            'submitted_at': proposal.submitted_at.isoformat(),
            'freelancer': {
                'id': proposal.freelancer.id,
                'name': f"{proposal.freelancer.first_name} {proposal.freelancer.last_name}",
                'email': proposal.freelancer.email
            },
            'project': {
                'id': proposal.project.id,
                'title': proposal.project.title,
                'description': proposal.project.description,
                'budget': proposal.project.budget
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Error fetching proposal: {str(e)}'}), 500