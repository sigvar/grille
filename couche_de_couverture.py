##Vector=group
##Couche_de_couverture=name
##Couche_de_polygones=vector
##pas_en_x=number 10300.0
##pas_en_y=number 6400.0
##enveloppe=boolean True
##uniquement_intersecte=boolean False
##nombre_essais_optimisation=number 0
# une valeur par defaut doit etre definie pour une variable numerique ici 10300mx6400m
# a parametrer selon vos besoins habituels...
"""
Ce script vise a faciliter l'utilisation de l'atlas du composeur d'impression.
Il genere une couche de couverture d'une autre couche adaptee a une echelle fixe definie.

L'enveloppe d'un objet est calculee, on en deduit le nombre de dalles qu'on repartit en les centrant sur l'objet

Il faut saisir
   la couche d'entree,
   la taille d'une dalle
   si l'on souhaite les coordonnees de l'enveloppe de l'objet d'origine
   si on ne conserve que les cases sans intersection avec le polygone
   si on indique un nombre d'essais d'optimisation, l'algorithme cherche a minimiser le nombre de cases par polygones
     en deplaçant les cases par des pas d'une finesse proportionnelle a l'importance de cette valeur, il ne conserve que
     les cases sans intersection avec le polygone

Comme les colonnes de la table d'origine sont reprises et que des colonnes sont ajoutees, en cas de conflit de nom
le script s'arrete.

La couche de sortie en plus des attributs conserves presente 5 attributs supplementaires
 'id_poly'       un entier pour chaque objet d'origine
 'ord_x_grid'    un entier pour chaque ligne de dalles de chaque 'id_poly'
 'ord_y_grid'    un entier pour chaque colonne de dalles de chaque 'id_poly'
 'id_grid'       un entier unique par dalle
 'ord_poly_grid' un entier unique par dalle pour chaque 'id_poly'

Et si on a demande les coordonnees de l'enveloppe de l'objet d'origine
 'min_x_poly'    un double pour la valeur x min
 'max_x_poly'    un double pour la valeur x max
 'min_y_poly'    un double pour la valeur y min
 'max_y_poly'    un double pour la valeur y max

On peut filtrer l'affichage de la grille quand un composeur est actif en utilisant dans le style une regle comme :
 "id_objet" = attribute( $atlasfeature, 'id_objet' )

V1.b du 27 mai 2016 os@i-carre.net
V1.1 du 27 mai 2016 jean-christophe.baudin@onema.fr
V1.2 du 29 mai 2016 os@i-carre.net
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

# pre-traitement des variables
nombre_essais_optimisation = min(50, int(max(0, nombre_essais_optimisation))) # on limite a 50, un tableau 101x101 c'est deja pas mal !
if nombre_essais_optimisation > 0:
    uniquement_intersecte = True

essais_optimisation = range(-nombre_essais_optimisation, nombre_essais_optimisation + 1)

layer = processing.getObject(Couche_de_polygones)
provider = layer.dataProvider()
fields = provider.fields()

grille = QgsVectorLayer("Polygon", "Couche_de_couverture_de_"+ str(layer.name()), "memory")
QgsMapLayerRegistry.instance().addMapLayer(grille)
dp_grille = grille.dataProvider()

attributs_sup = ('id_poly', 'ord_x_grid', 'ord_y_grid', 'id_grid', 'ord_poly_grid')
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

id_poly = 0
grille.startEditing()
id_grid = 0
for feature in feats:
    progress.setPercentage(int(100 * id_poly / nb_feat))

    # get the feature bounding box
    feat_geom = feature.geometry().boundingBox()
    min_x_poly = feat_geom.xMinimum()
    max_x_poly = feat_geom.xMaximum()
    min_y_poly = feat_geom.yMinimum()
    max_y_poly = feat_geom.yMaximum()

    # dimensions des cases/dalles
    nombre_case_x = arrondi_sup((max_x_poly - min_x_poly) / pas_en_x)
    nombre_case_y = arrondi_sup((max_y_poly - min_y_poly) / pas_en_y)
    milieu_x = milieu(min_x_poly, max_x_poly)
    milieu_y = milieu(min_y_poly, max_y_poly)
    minimum_x = milieu_x - pas_en_x * nombre_case_x / 2.0
    minimum_y = milieu_y - pas_en_y * nombre_case_y / 2.0
    ajustement_x = ((max_x_poly - min_x_poly) - nombre_case_x * pas_en_x) / 2. / max(1, nombre_essais_optimisation)
    ajustement_y = ((max_y_poly - min_y_poly) - nombre_case_y * pas_en_y) / 2. / max(1, nombre_essais_optimisation)

    # pour determiner une position du bloc de dalles minimisant le nombre de dalles on cree un
    # tableau des nombres de cases intersectant le polygone selon les decalages en x et y
    resultats = []
    for i in range(len(essais_optimisation)):
        resultats.append([])
        for j in range(len(essais_optimisation)):
            resultats[i].append(0)
    for ajustement_x_pas in essais_optimisation:
        for ajustement_y_pas in essais_optimisation:
            for case_x in range(nombre_case_x):
                for case_y in range(nombre_case_y):
                    rectangle = QgsGeometry.fromRect( \
                                    QgsRectangle( \
                                        minimum_x + case_x * pas_en_x + ajustement_x_pas * ajustement_x, \
                                        minimum_y + case_y * pas_en_y + ajustement_y_pas * ajustement_y, \
                                        minimum_x + (case_x + 1) * pas_en_x + ajustement_x_pas * ajustement_x, \
                                        minimum_y + (case_y + 1) * pas_en_y + ajustement_y_pas * ajustement_y))
                    if rectangle.intersects(feature.geometry()):
                        resultats[ajustement_x_pas + nombre_essais_optimisation][ajustement_y_pas + nombre_essais_optimisation] += 1
    # calcul du minimum des cases selon les decalages en x et y
    minimum_case = resultats[0][0]
    for lig in resultats:
        for col in lig:
            minimum_case = min(minimum_case, col)
    # on ne conserve que ces dernieres qu'on pondere par la position par rapport au moindre decalage
    for i in range(len(essais_optimisation)):
        for j in range(len(essais_optimisation)):
            if resultats[i][j] > minimum_case:
                resultats[i][j] = -1 # les autres sont mises à une valeur negative
            else:
                # distance au centre
                resultats[i][j] = (i - nombre_essais_optimisation)**2 + (j - nombre_essais_optimisation)**2
                minimum_pondere = resultats[i][j] # pour en avoir un
    # on cherche le minimum de ces positions ponderees
    for lig in resultats:
        for col in lig:
            if col >= 0:
                minimum_pondere = min(minimum_pondere, col)
    # on determine une case valant le minimum et on stocke ses coordonnees
    for i in range(len(essais_optimisation)):
        for j in range(len(essais_optimisation)):
            if resultats[i][j] == minimum_pondere:
                ajustement_x_pas = i - nombre_essais_optimisation
                ajustement_y_pas = j - nombre_essais_optimisation
                #break
    # on peut maintenant creer la grille pour ce polygone
    id_poly += 1
    ord_x_grid = 0
    ord_poly_grid = 0
    for case_x in range(nombre_case_x):
        ord_x_grid += 1
        ord_y_grid = 0
        for case_y in range(nombre_case_y):
            rectangle = QgsGeometry.fromRect( \
                            QgsRectangle( \
                                minimum_x + case_x * pas_en_x + ajustement_x_pas * ajustement_x, \
                                minimum_y + case_y * pas_en_y + ajustement_y_pas * ajustement_y, \
                                minimum_x + (case_x + 1) * pas_en_x + ajustement_x_pas * ajustement_x, \
                                minimum_y + (case_y + 1) * pas_en_y + ajustement_y_pas * ajustement_y))
            if not uniquement_intersecte or (uniquement_intersecte and rectangle.intersects(feature.geometry())):
                ord_y_grid += 1
                id_grid += 1
                ord_poly_grid += 1
                new_feat = QgsFeature()
                new_feat.setGeometry(rectangle)
                attribute_values = feature.attributes()[:]
                attribute_values.extend([id_poly, ord_x_grid, ord_y_grid, id_grid, ord_poly_grid])
                if enveloppe:
                    attribute_values.extend([min_x_poly, max_x_poly, min_y_poly, max_y_poly])
                new_feat.setAttributes(attribute_values)
                dp_grille.addFeatures([new_feat])        # ajoute les geom et valeurs des enregistrements
                dp_grille.updateExtents()                # quitte le mode edition et enregistre les modifs

grille.commitChanges()

iface.mapCanvas().refresh()
#QMessageBox.information(None,"DEBUGn: " , "texte")

