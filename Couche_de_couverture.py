##Vector=group
##Couche_de_couverture=name
##Couche_de_polygones=vector
##pas_en_x=number 15000.0
##pas_en_y=number 15000.0
##enveloppe=boolean True
# une valeur par defaut doit etre definie pour une variable numerique ici 15000m
# A parametrer selon vos besoins habituels...
"""
Ce script vise a  faciliter l'utilisation du plugin Atlas dans le composeur d'impression
Il genere une couche de couverture adaptee a une echelle voulue definie par pas_en_x et pas_en_y
Ce script utilise largement le travail de M.SAVOYE Olivier
voir mail  du mercredi 25 mai 2016 12:22 de  labo.qgis@developpement-durable.gouv.fr :
Objet : [NEWS] ***Pas de controle antivirus***Re: [labo.qgis] Composeur d'impression echelle fixe
Il a ete repris par M. MASSE Christophe le 27 05 2015
V1.1 du  27 mai 2015
jean-christophe.baudin@onema.fr
"""
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os
import sys
from processing import *

# fonctions utiles
arrondi_sup = lambda x : int(x) if x == int(x) * 1. else int(round(x + .5))
milieu = lambda a, b : a + (b - a) / 2

layer = processing.getObject(Couche_de_polygones)
provider = layer.dataProvider()
fields = provider.fields()
nb_element = 0

grille = QgsVectorLayer("Polygon", "Couche_de_couverture_de_"+ str(layer.name()), "memory")
QgsMapLayerRegistry.instance().addMapLayer(grille)
dp_grille = grille.dataProvider()

attributs_sup = ('id_poly', 'ord_x_grid', 'ord_y_grid', 'id_grid')
attributs_sup_env = ('min_x_poly', 'max_x_poly', 'min_y_poly', 'max_y_poly', )
for f in fields:
    dp_grille.addAttributes([f])
    field_name = f.name()
    if field_name in attributs_sup:
        raise NameError('le champ %s existe deja, modifier le code du script ou la table '%field_name)
    if enveloppe and field_name in attributs_sup_env:
        raise NameError('le champ %s existe deja, modifier le code du script ou la table '%field_name)
for attr in attributs_sup:
    dp_grille.addAttributes([QgsField(attr, QVariant.Int)])
if enveloppe:
    for attr in attributs_sup_env:
        dp_grille.addAttributes([QgsField(attr, QVariant.Double)])

feats = processing.features(layer)
nb_feat = len(feats)

grille.startEditing()
nb_grid = 0
for feature in feats:
    progress.setPercentage(int(100 * nb_element / nb_feat))
    nb_element += 1
    feat_attributes = feature.attributes()

    # get the feature bounding box
    feat_geom = feature.geometry().boundingBox()
    xmin, xmax, ymin, ymax = feat_geom.xMinimum(), feat_geom.xMaximum(), feat_geom.yMinimum(), feat_geom.yMaximum()

    # dimensions des cases/dalles ;)
    nombre_case_x = arrondi_sup((xmax - xmin) / pas_en_x)
    nombre_case_y = arrondi_sup((ymax - ymin) / pas_en_y)
    milieu_x = milieu(xmin, xmax)
    milieu_y = milieu(ymin, ymax)
    minimum_x = milieu_x - pas_en_x * nombre_case_x / 2.0
    minimum_y = milieu_y - pas_en_y * nombre_case_y / 2.0

    nbc_x = 0
    for case_x in range(nombre_case_x):
        nbc_x += 1
        nbc_y = 0
        for case_y in range(nombre_case_y):
            nbc_y += 1
            nb_grid += 1
            x_min = minimum_x + case_x * pas_en_x
            x_max = minimum_x + (case_x + 1) * pas_en_x
            y_min = minimum_y + case_y * pas_en_y
            y_max = minimum_y + (case_y + 1) * pas_en_y
            new_feat = QgsFeature()
            new_feat.setGeometry(QgsGeometry().fromPolygon([[QgsPoint(x_min, y_min),\
                                                             QgsPoint(x_min, y_max),\
                                                             QgsPoint(x_max, y_max),\
                                                             QgsPoint(x_max, y_min),\
                                                             QgsPoint(x_min, y_min)]]))
            attribute_values = feat_attributes[:]
            attribute_values.append(nb_element)
            attribute_values.append(nbc_x)
            attribute_values.append(nbc_y)
            attribute_values.append(nb_grid)
            if enveloppe:
                attribute_values.append(xmin)
                attribute_values.append(xmax)
                attribute_values.append(ymin)
                attribute_values.append(ymax)
            new_feat.setAttributes(attribute_values)
            # ajoute les geom et valeurs des enregistrements,
            dp_grille.addFeatures([new_feat])
            # quitte le mode edition et enregistre les modifs:
            dp_grille.updateExtents()

grille.commitChanges()

iface.mapCanvas().refresh()
#QMessageBox.information(None,"DEBUGn: " , "texte")

