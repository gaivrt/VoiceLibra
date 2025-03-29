from flask import jsonify, request, send_file, current_app
from pathlib import Path

def setup_routes(app):
    @app.route('/api/status/<job_id>', methods=['GET'])
    def get_job_status(job_id):
        return jsonify({
            "status": "processing", 
            "progress": 65,
            "message": "正在处理第3章..."
        })
    
    @app.route('/api/download/<file_id>', methods=['GET'])
    def download_audio(file_id):
        file_path = Path(current_app.config['OUTPUTS_DIR']) / f"{file_id}.mp3"
        if file_path.exists():
            return send_file(str(file_path), as_attachment=True)
        else:
            return jsonify({"error": "文件不存在"}), 404
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "engine": "fish-speech"
        })