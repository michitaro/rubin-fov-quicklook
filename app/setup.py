from pathlib import Path

from setuptools import find_packages, setup

HERE = Path(__file__).parent

setup(
    name='quicklook',
    version='0.1.0',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    python_requires='==3.11.*',
    install_requires=[
        'pydantic-settings',
        'fastapi',
        'uvicorn',
        'uvicorn[standard]',
        'flask',
        'minio',
        'astropy==5.2.2',
        'numpy==1.*',
        'rtree',
        'zstandard',
        'aiohttp',
        'SQLAlchemy==2.*',
        'alembic==1.12.*',
        'psycopg2-binary',
        'tqdm',
    ],
    extras_require={
        'dev': [
            'pdbpp',
            'requests',
            'pytest-watch',
            'pytest-cov',
            'pytest-env',
            'pytest-asyncio',
            'pytest-watch',
            'black',
        ],
    },
)
