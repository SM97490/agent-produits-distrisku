#!/usr/bin/env python3
"""
Version simplifiée de l'agent - Test de déploiement
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import os
import tempfile
import uuid
from datetime import datetime
import logging

# Configuration
app = Flask(__name__)
CORS(app)

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables globales pour le suivi des tâches
tasks = {}

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Endpoint de santé"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0-simple'
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload et traitement du fichier"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        # Vérifier le format
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Format non supporté. Utilisez Excel (.xlsx ou .xls)'}), 400
        
        # Créer un ID de tâche
        task_id = str(uuid.uuid4())
        
        # Sauvegarder le fichier temporairement
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, f"input_{task_id}.xlsx")
        file.save(input_path)
        
        # Traitement simple
        try:
            # Lire le fichier Excel
            df = pd.read_excel(input_path)
            logger.info(f"Fichier lu: {len(df)} lignes")
            
            # Vérifier les colonnes requises
            required_cols = ['SKU', 'Prix d\'achat']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                return jsonify({
                    'error': f'Colonnes manquantes: {", ".join(missing_cols)}',
                    'colonnes_trouvees': list(df.columns)
                }), 400
            
            # Traitement simple des données
            result_df = df.copy()
            
            # Calculs de prix
            result_df['Prix de revient'] = result_df['Prix d\'achat'] * 1.16
            result_df['Prix de vente'] = result_df['Prix de revient'] / 0.65
            
            # Ajout de colonnes basiques
            result_df['Libellé gestion'] = result_df['SKU'] + ' - Produit'
            result_df['Description devis'] = 'Description technique du produit ' + result_df['SKU']
            result_df['Description e-commerce'] = 'Produit ' + result_df['SKU'] + ' - Idéal pour vos besoins professionnels'
            result_df['Statut validation'] = 'Validé (version simple)'
            
            # Sauvegarder le résultat
            output_path = os.path.join(temp_dir, f"output_{task_id}.xlsx")
            result_df.to_excel(output_path, index=False)
            
            # Stocker les informations de la tâche
            tasks[task_id] = {
                'status': 'completed',
                'input_file': input_path,
                'output_file': output_path,
                'temp_dir': temp_dir,
                'created_at': datetime.now(),
                'products_processed': len(result_df),
                'products_validated': len(result_df)
            }
            
            return jsonify({
                'task_id': task_id,
                'status': 'completed',
                'message': f'Traitement terminé: {len(result_df)} produits traités',
                'products_processed': len(result_df),
                'products_validated': len(result_df)
            })
            
        except Exception as e:
            logger.error(f"Erreur de traitement: {str(e)}")
            return jsonify({'error': f'Erreur de traitement: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Erreur upload: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@app.route('/status/<task_id>')
def get_status(task_id):
    """Obtenir le statut d'une tâche"""
    if task_id not in tasks:
        return jsonify({'error': 'Tâche non trouvée'}), 404
    
    task = tasks[task_id]
    return jsonify({
        'task_id': task_id,
        'status': task['status'],
        'products_processed': task.get('products_processed', 0),
        'products_validated': task.get('products_validated', 0),
        'created_at': task['created_at'].isoformat()
    })

@app.route('/download/<task_id>')
def download_result(task_id):
    """Télécharger le fichier résultat"""
    if task_id not in tasks:
        return jsonify({'error': 'Tâche non trouvée'}), 404
    
    task = tasks[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': 'Traitement non terminé'}), 400
    
    output_file = task['output_file']
    if not os.path.exists(output_file):
        return jsonify({'error': 'Fichier résultat non trouvé'}), 404
    
    return send_file(
        output_file,
        as_attachment=True,
        download_name=f'produits_enrichis_{task_id[:8]}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

