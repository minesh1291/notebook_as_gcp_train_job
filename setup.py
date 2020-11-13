from setuptools import setup, find_packages

REQUIRED_PACKAGES = []

setup(name="trainer",
      packages=["trainer"],
      package_dir={'trainer':'trainer'},
      version="1.0",
      install_requires=REQUIRED_PACKAGES,
      
      # include_package_data=True,
      # #package_data={'egro_zero': ['egro_zero/*.yml']},
      # data_files = [('egro_zero',['egro_zero/rules.yml','egro_zero/usecases.yml'])]
     )
