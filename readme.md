=========================
Script de génération de tickets et cahiers de transportateur par Mokhtar Mohamed Moussa et copyright de MISC.

============
Installation (windows)
1. Installer python3.10 : https://www.python.org/downloads/release/python-31011/
 attention bien cocher la case ajouter python au PATH
2. executer python3.10.exe -m pip install -r requirement.txt

==============
Utilisation
Deux uses cases possible: 

Génération de cahier :

python3.10.exe -m test --pdftemplate ./tamplatespvierge2.pdf --gare Timbedra --montant 10000 --annee 2025 --barcodeprefix 5443873 --output res.pdf --min 1 --max 10

Génération de tickets:

python3.10.exe -m tickets --pdftemplate ./tamplatespvierge2.pdf --gare Timbedra --montant 10000 --annee 2025 --barcodeprefix 5443873 --output res.pdf --min 1 --max 10

les pdfs générés sont enregistrés dans le dossier output/