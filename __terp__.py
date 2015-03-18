{
    "name": "Tigernix Export", 
    "version": "1.0",
    "depends": ["base"],
    "author": "Tigernix",
    "category": "Custom Development",
    "description": """
    Tigernix's Custom Export function based on object with:
    - Field Selection
    - Field Filtering
    - Export to CSV
    - Export to PDF
    """,
    "init_xml": [],
    'update_xml': [
        'csv_report_view.xml',
        'pdf_report_view.xml',
        'tigernix_export_view.xml',
        'security/ir.model.access.csv',

    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}