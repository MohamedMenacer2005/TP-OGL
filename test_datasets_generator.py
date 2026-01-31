#!/usr/bin/env python3
"""
TEST DATASET GENERATOR
======================
Génère les jeux de données de test standardisés pour validation interne.
"""

import os
import json
from pathlib import Path
from test_datasets.syntax_errors import SYNTAX_ERROR_DATASETS
from test_datasets.style_issues import STYLE_ISSUE_DATASETS
from test_datasets.logic_errors import LOGIC_ERROR_DATASETS


class TestDatasetGenerator:
    """Génère les répertoires de test standardisés."""
    
    def __init__(self, base_dir: str = "test_datasets/generated"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_syntax_tests(self):
        """Crée les fichiers de test syntaxe."""
        syntax_dir = self.base_dir / "syntax_errors"
        syntax_dir.mkdir(exist_ok=True)
        
        for i, dataset in enumerate(SYNTAX_ERROR_DATASETS, 1):
            filepath = syntax_dir / f"error_{i}.py"
            with open(filepath, 'w') as f:
                f.write(dataset['code'])
            
            # Créer le fichier attendu
            expected_file = syntax_dir / f"error_{i}_expected.py"
            with open(expected_file, 'w') as f:
                f.write(dataset['expected_fix'])
        
        # Créer index.json
        index = {
            'category': 'Syntax Errors',
            'count': len(SYNTAX_ERROR_DATASETS),
            'datasets': [
                {
                    'id': i,
                    'name': ds['name'],
                    'file': f"error_{i}.py",
                    'expected_file': f"error_{i}_expected.py"
                }
                for i, ds in enumerate(SYNTAX_ERROR_DATASETS, 1)
            ]
        }
        
        with open(syntax_dir / "index.json", 'w') as f:
            json.dump(index, f, indent=2)
        
        return syntax_dir
    
    def generate_style_tests(self):
        """Crée les fichiers de test style."""
        style_dir = self.base_dir / "style_issues"
        style_dir.mkdir(exist_ok=True)
        
        for i, dataset in enumerate(STYLE_ISSUE_DATASETS, 1):
            filepath = style_dir / f"issue_{i}.py"
            with open(filepath, 'w') as f:
                f.write(dataset['code'])
            
            # Créer le fichier attendu
            expected_file = style_dir / f"issue_{i}_expected.py"
            with open(expected_file, 'w') as f:
                f.write(dataset['expected_fix'])
        
        # Créer index.json
        index = {
            'category': 'Style Issues',
            'count': len(STYLE_ISSUE_DATASETS),
            'datasets': [
                {
                    'id': i,
                    'name': ds['name'],
                    'file': f"issue_{i}.py",
                    'expected_file': f"issue_{i}_expected.py"
                }
                for i, ds in enumerate(STYLE_ISSUE_DATASETS, 1)
            ]
        }
        
        with open(style_dir / "index.json", 'w') as f:
            json.dump(index, f, indent=2)
        
        return style_dir
    
    def generate_logic_tests(self):
        """Crée les fichiers de test logique."""
        logic_dir = self.base_dir / "logic_errors"
        logic_dir.mkdir(exist_ok=True)
        
        for i, dataset in enumerate(LOGIC_ERROR_DATASETS, 1):
            filepath = logic_dir / f"bug_{i}.py"
            with open(filepath, 'w') as f:
                f.write(dataset['code'])
            
            # Créer le fichier attendu
            expected_file = logic_dir / f"bug_{i}_expected.py"
            with open(expected_file, 'w') as f:
                f.write(dataset['expected_fix'])
        
        # Créer index.json
        index = {
            'category': 'Logic Errors',
            'count': len(LOGIC_ERROR_DATASETS),
            'datasets': [
                {
                    'id': i,
                    'name': ds['name'],
                    'file': f"bug_{i}.py",
                    'expected_file': f"bug_{i}_expected.py"
                }
                for i, ds in enumerate(LOGIC_ERROR_DATASETS, 1)
            ]
        }
        
        with open(logic_dir / "index.json", 'w') as f:
            json.dump(index, f, indent=2)
        
        return logic_dir
    
    def generate_all(self):
        """Génère tous les jeux de test."""
        print("[*] Génération des jeux de données de test...")
        
        syntax_dir = self.generate_syntax_tests()
        print(f"✅ Tests syntaxe générés: {syntax_dir}")
        
        style_dir = self.generate_style_tests()
        print(f"✅ Tests style générés: {style_dir}")
        
        logic_dir = self.generate_logic_tests()
        print(f"✅ Tests logique générés: {logic_dir}")
        
        # Créer manifest global
        manifest = {
            'generated_at': __import__('datetime').datetime.now().isoformat(),
            'directories': {
                'syntax_errors': str(syntax_dir),
                'style_issues': str(style_dir),
                'logic_errors': str(logic_dir)
            },
            'total_tests': (
                len(SYNTAX_ERROR_DATASETS) +
                len(STYLE_ISSUE_DATASETS) +
                len(LOGIC_ERROR_DATASETS)
            ),
            'description': 'Jeu de données standardisé pour validation interne du système multi-agent'
        }
        
        manifest_file = self.base_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\n✅ Manifest créé: {manifest_file}")
        print(f"✅ Total tests générés: {manifest['total_tests']}")
        
        return self.base_dir


if __name__ == "__main__":
    generator = TestDatasetGenerator()
    generator.generate_all()
