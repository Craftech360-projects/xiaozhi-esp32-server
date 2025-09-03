"""
Educational RAG Configuration
Loads configuration from .config.yaml and provides default settings
"""

import os
from typing import Dict, Any
from config.config_loader import load_config

def get_educational_rag_config() -> Dict[str, Any]:
    """Get educational RAG configuration from .config.yaml"""
    try:
        # Get config from .config.yaml via xiaozhi-server's config system
        full_config = load_config()
        
        # Extract educational_rag config from Memory section
        if ('Memory' in full_config and 
            'educational_rag' in full_config['Memory']):
            config = full_config['Memory']['educational_rag']
            
            # Override with correct Qdrant settings from RAG project
            config['qdrant_url'] = 'https://1198879c-353e-49b1-bfab-8f74004aaf6d.eu-central-1-0.aws.cloud.qdrant.io'
            config['qdrant_api_key'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.wKcnr3q8Sq4tb7JzPGnZbuxm9XpfDNutdfFD8mCDlrc'
            
            # Set correct collection names from RAG project
            config.setdefault('subjects', {})
            config['subjects']['mathematics'] = {
                'collection_name': 'class-6-mathematics',
                'enabled': True,
                'agent_class': 'MathematicsAgent'
            }
            config['subjects']['science'] = {
                'collection_name': 'class-6-science',
                'enabled': True,
                'agent_class': 'ScienceAgent'
            }
            
            # Set defaults if not specified
            config.setdefault('type', 'educational_rag')
            config.setdefault('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')  # 384 dims to match RAG collections
            config.setdefault('multi_subject_support', True)
            config.setdefault('enable_cache', True)
            config.setdefault('cache_ttl', 3600)
            config.setdefault('score_threshold', 0.2)
            config.setdefault('max_results', 5)
            config.setdefault('enable_step_by_step', True)
            config.setdefault('enable_practice_suggestions', True)
            config.setdefault('include_sources', True)
            config.setdefault('include_related_topics', True)
            config.setdefault('standard', 6)
            config.setdefault('subject', 'mathematics')
            config.setdefault('collection_name', 'class-6-mathematics')
            
            return config
        else:
            # Return default configuration
            return get_default_config()
            
    except Exception as e:
        print(f"Error loading educational RAG config: {e}")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """Default configuration for educational RAG with correct Qdrant settings"""
    return {
        'type': 'educational_rag',
        'qdrant_url': 'https://1198879c-353e-49b1-bfab-8f74004aaf6d.eu-central-1-0.aws.cloud.qdrant.io',
        'qdrant_api_key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.wKcnr3q8Sq4tb7JzPGnZbuxm9XpfDNutdfFD8mCDlrc',
        'collection_name': 'class-6-mathematics',
        'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',  # Same as RAG project
        'multi_subject_support': True,
        'subjects': {
            'mathematics': {
                'collection_name': 'class-6-mathematics',
                'enabled': True,
                'agent_class': 'MathematicsAgent'
            },
            'science': {
                'collection_name': 'class-6-science',
                'enabled': True, 
                'agent_class': 'ScienceAgent'
            }
        },
        'subject': 'mathematics',
        'standard': 6,
        'enable_cache': True,
        'cache_ttl': 3600,
        'score_threshold': 0.2,
        'max_results': 5,
        'enable_step_by_step': True,
        'enable_practice_suggestions': True,
        'include_sources': True,
        'include_related_topics': True
    }

# Global config instance
EDUCATIONAL_RAG_CONFIG = get_educational_rag_config()