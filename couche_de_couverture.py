##Vector=group
##couche_de_couverture=name
##couche_de_polygones=vector
##pas_en_x=number 7000.0
##pas_en_y=number 6000.0
##overlap_percentage=number 0
##dalle=boolean False
##enveloppe=boolean False
##uniquement_intersecte=boolean False
##pas_du_decalage=number 0
"""
 couche_de_couverture
======================

    /***************************************************************************
     *                                                                         *
     *   This program is free software; you can redistribute it and/or modify  *
     *   it under the terms of the GNU General Public License as published by  *
     *   the Free Software Foundation; either version 2 of the License, or     *
     *   (at your option) any later version.                                   *
     *                                                                         *
     ***************************************************************************/

Ce script vise a faciliter l'utilisation de l'atlas du composeur d'impression
-----------------------------------------------------------------------------

Il genere une couche de couverture d'une autre couche adaptee a une echelle fixe definie.

L'enveloppe d'un objet est calculee, on en deduit le nombre de dalles qu'on repartit en les centrant sur l'objet.

Il faut saisir :
- la couche d'entree,
- la taille d'une dalle,
- un pourcentage de recouvrement autour du polygone
- si on souhaite les coordonnees de chaque dalle,
- si on souhaite les coordonnees de l'enveloppe de l'objet d'origine,
- si on ne conserve que les cases sans intersection avec le polygone,
- et quand on indique un pas de decalage, l'algorithme cherche a minimiser le nombre de cases par polygones
     en deplaçant les cases par des pas de cette valeur, il ne conserve que les cases sans intersection
     avec le polygone. La taille du pas est limitée au centième de la taille d'une dalle et ca sera TRES lent

Comme les colonnes de la table d'origine sont reprises et que des colonnes sont ajoutees, en cas de conflit de nom
le script s'arrete.

La couche de sortie en plus des attributs conserves presente 5 attributs supplementaires :
- 'id_poly'       un entier pour chaque objet d'origine
- 'ord_x_grid'    un entier pour chaque ligne de dalles de chaque 'id_poly'
- 'ord_y_grid'    un entier pour chaque colonne de dalles de chaque 'id_poly'
- 'id_grid'       un entier unique par dalle
- 'ord_poly_grid' un entier unique par dalle pour chaque 'id_poly'

Et si on a demande les coordonnees de la dalle :
- 'min_x_grid'    un double pour la valeur x min
- 'max_x_grid'    un double pour la valeur x max
- 'min_y_grid'    un double pour la valeur y min
- 'max_y_grid'    un double pour la valeur y max

Et si on a demande les coordonnees de l'enveloppe de l'objet d'origine :
- 'min_x_poly'    un double pour la valeur x min
- 'max_x_poly'    un double pour la valeur x max
- 'min_y_poly'    un double pour la valeur y min
- 'max_y_poly'    un double pour la valeur y max

On peut filtrer l'affichage de la grille quand un composeur est actif en utilisant dans le style une regle comme :
- "id_objet" = attribute( $atlasfeature, 'id_objet' )

Versions :
- V1.b du 27 mai 2016
- V1.1 du 27 mai 2016 jean-christophe.baudin@onema.fr
- V1.2 du 29 mai 2016
- V1.3 du 31 mai 2016
- V1.4 du 31 mai 2016 changement complet du traitement des optimisations
"""
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os
import sys
from processing import *
from math import ceil

# limite du nombre maximum de deplacement
DEMI_MAX_DEPLACEMENT = 150 # plus de 12 millions de calculs pour les 153 communes du Var pour en moyenne 4 dalles

# fonction utile
milieu = lambda a, b : a + (b - a) / 2.0

# pre-traitement des variables
# faut un minimum ;)
if pas_en_x <= 0 or pas_en_y <= 0:
    raise NameError('la taille de la dalle n\'est pas suffisante')

# trop c'est trop !
if overlap_percentage > 45:
    QMessageBox.information(None,"Information:", " You choose %s\%. for overlap percentage.\nIt will be reduced to 45% ...\nWhy not try something around 10% next time ? "%overlap_percentage)
    percent = 45

# on ne garde que les dalles qui intersectent le polygone si on a defini un pas de decalage
if pas_du_decalage > 0:
    uniquement_intersecte = True
    # plus de pb memoire mais ca va etre horriblement long
    if max(pas_en_x, pas_en_y) / pas_du_decalage > DEMI_MAX_DEPLACEMENT:
        pas_du_decalage = int(ceil(max(pas_en_x, pas_en_y) / DEMI_MAX_DEPLACEMENT)) * 5
        raise NameError("You choose a too small value for pas_du_decalage. Why not try something around %s next time ? "%pas_du_decalage)

# ouverture de la couche support d'entree
layer = processing.getObject(couche_de_polygones)
provider = layer.dataProvider()
fields = provider.fields()
feats = processing.features(layer)
nb_feat = len(feats)

# preparation de la couche grille
grille = QgsVectorLayer("Polygon", "couche_de_couverture_de_"+ str(layer.name()), "memory")
QgsMapLayerRegistry.instance().addMapLayer(grille)
dp_grille = grille.dataProvider()

# definition des attributs supplementaires
attributs_sup = ('id_poly', 'ord_x_grid', 'ord_y_grid', 'id_grid', 'ord_poly_grid')
attributs_sup_grid = ('min_x_grid', 'max_x_grid', 'min_y_grid', 'max_y_grid', )
attributs_sup_env = ('min_x_poly', 'max_x_poly', 'min_y_poly', 'max_y_poly', )
for f in fields:
    dp_grille.addAttributes([f])
    field_name = f.name()
    # en concurrence avec un attribut supplementaire
    if field_name in attributs_sup or \
        (dalle and field_name in attributs_sup_grid) or \
        (enveloppe and field_name in attributs_sup_env):
        raise NameError('le champ %s existe deja, modifier le code du script ou la table '%field_name)
# ajout des attributs supplementaires standards
for attr in attributs_sup:
    dp_grille.addAttributes([QgsField(attr, QVariant.Int)])
# ajout des attributs supplementaires de coordonnees de la dalle
if dalle:
    for attr in attributs_sup_grid:
        dp_grille.addAttributes([QgsField(attr, QVariant.Double)])
# ajout des attributs supplementaires de coordonnees de l'enveloppe du polygone (buffurise) support
if enveloppe:
    for attr in attributs_sup_env:
        dp_grille.addAttributes([QgsField(attr, QVariant.Double)])

id_poly = 0
id_grid = 0
grille.startEditing()
# pour tous les polygones
for feature in feats:
    progress.setPercentage(int(100 * id_poly / nb_feat))

    # get the feature bounding box
    bounding_geom = feature.geometry().boundingBox()
    min_x_poly = bounding_geom.xMinimum()
    max_x_poly = bounding_geom.xMaximum()
    min_y_poly = bounding_geom.yMinimum()
    max_y_poly = bounding_geom.yMaximum()
    buffer_geom = feature.geometry()

    # s'il est demande un buffer autour de l'objet
    if overlap_percentage > 0:
        buffer_geom = feature.geometry().buffer(overlap_percentage / 100 * max((max_x_poly - min_x_poly), (max_y_poly - min_y_poly)), 10)
        bounding_geom = buffer_geom.boundingBox()
        min_x_poly = bounding_geom.xMinimum()
        max_x_poly = bounding_geom.xMaximum()
        min_y_poly = bounding_geom.yMinimum()
        max_y_poly = bounding_geom.yMaximum()

    # dimensions des cases/dalles
    taille_poly_x = max_x_poly - min_x_poly
    taille_poly_y = max_y_poly - min_y_poly
    nombre_case_x = int(ceil(taille_poly_x / pas_en_x))
    nombre_case_y = int(ceil(taille_poly_y / pas_en_y))
    milieu_x = milieu(min_x_poly, max_x_poly)
    milieu_y = milieu(min_y_poly, max_y_poly)
    minimum_x_centre = milieu_x - pas_en_x * nombre_case_x / 2.0
    minimum_y_centre = milieu_y - pas_en_y * nombre_case_y / 2.0
    marge_x = nombre_case_x * pas_en_x - taille_poly_x
    marge_y = nombre_case_y * pas_en_y - taille_poly_y

    # pour ne pas deplacer les dalles en dehors de l'emprise du polygone bufferise quand
    # on calculera la grille deplacee en limite
    limite_decalage_x = lambda x : -marge_x / 2.0 if x < -marge_x / 2.0 else x if x < marge_x / 2.0 else marge_x / 2.0
    limite_decalage_y = lambda y : -marge_y / 2.0 if y < -marge_y / 2.0 else y if y < marge_y / 2.0 else marge_y / 2.0

    # peut-on chercher a optimiser le nombre de dalles ?
    if nombre_case_x * nombre_case_y <= 2 or pas_du_decalage == 0: # pas d'optimisation possible ou desiree
        minimum_ajustement_x_pas = 0
        minimum_ajustement_y_pas = 0
    else:
        # on calcule le nombre de decalages possibles, arrondi superieur pour aller a la limite
        demi_nombre_essais_decalage_x = int(ceil(marge_x / 2.0 / pas_du_decalage))
        demi_nombre_essais_decalage_y = int(ceil(marge_y / 2.0 / pas_du_decalage))
        # nombre de case minimum intersectant le polygone
        minimum_case = 0
        # on parcours tous les decalages possibles
        for ajustement_x_pas in range(-demi_nombre_essais_decalage_x, demi_nombre_essais_decalage_x + 1):
            for ajustement_y_pas in range(-demi_nombre_essais_decalage_y, demi_nombre_essais_decalage_y + 1):
                nombre_intersection = 0
                # on cherche pour toutes les dalles si elles intersectent le polygone bufferise
                for case_x in range(nombre_case_x):
                    for case_y in range(nombre_case_y):
                        rectangle = QgsGeometry.fromRect( \
                                        QgsRectangle( \
                                            minimum_x_centre + case_x * pas_en_x + limite_decalage_x(ajustement_x_pas * pas_du_decalage), \
                                            minimum_y_centre + case_y * pas_en_y + limite_decalage_y(ajustement_y_pas * pas_du_decalage), \
                                            minimum_x_centre + (case_x + 1) * pas_en_x + limite_decalage_x(ajustement_x_pas * pas_du_decalage), \
                                            minimum_y_centre + (case_y + 1) * pas_en_y + limite_decalage_y(ajustement_y_pas * pas_du_decalage)))
                        # l'intersection se fait avec le polygone bufferise
                        if rectangle.intersects(buffer_geom):
                            nombre_intersection += 1
                # on conserve la premiere valeur minimale proche de la moyenne en distance
                if nombre_intersection < minimum_case or minimum_case == 0:
                    ponderation = (ajustement_x_pas - demi_nombre_essais_decalage_x)**2 + (ajustement_y_pas - demi_nombre_essais_decalage_y)**2
                    minimum_case = nombre_intersection
                    minimum_ajustement_x_pas = ajustement_x_pas
                    minimum_ajustement_y_pas = ajustement_y_pas
                    minimum_ponderation = ponderation
                elif nombre_intersection == minimum_case:
                    ponderation = (ajustement_x_pas - demi_nombre_essais_decalage_x)**2 + (ajustement_y_pas - demi_nombre_essais_decalage_y)**2
                    if ponderation < minimum_ponderation:
                        minimum_case = nombre_intersection
                        minimum_ajustement_x_pas = ajustement_x_pas
                        minimum_ajustement_y_pas = ajustement_y_pas
                        minimum_ponderation = ponderation

    # on a determine la position des dalles, on peut maintenant creer la grille pour ce polygone
    id_poly += 1
    ord_x_grid = 0
    ord_poly_grid = 0
    for case_x in range(nombre_case_x):
        ord_x_grid += 1
        ord_y_grid = 0
        for case_y in range(nombre_case_y):
            # on recalcule la dalle
            min_x_grid = minimum_x_centre + case_x * pas_en_x + limite_decalage_x(minimum_ajustement_x_pas * pas_du_decalage)
            min_y_grid = minimum_y_centre + case_y * pas_en_y + limite_decalage_y(minimum_ajustement_y_pas * pas_du_decalage)
            max_x_grid = minimum_x_centre + (case_x + 1) * pas_en_x + limite_decalage_x(minimum_ajustement_x_pas * pas_du_decalage)
            max_y_grid = minimum_y_centre + (case_y + 1) * pas_en_y + limite_decalage_y(minimum_ajustement_y_pas * pas_du_decalage)
            rectangle = QgsGeometry.fromRect(QgsRectangle( min_x_grid, min_y_grid, max_x_grid, max_y_grid))
            # l'intersection se fait avec le polygone bufferise
            if not uniquement_intersecte or (uniquement_intersecte and rectangle.intersects(buffer_geom)):
                ord_y_grid += 1
                id_grid += 1
                ord_poly_grid += 1
                new_feat = QgsFeature()
                new_feat.setGeometry(rectangle)
                attribute_values = feature.attributes()[:]
                attribute_values.extend([id_poly, ord_x_grid, ord_y_grid, id_grid, ord_poly_grid])
                if dalle:
                    attribute_values.extend([min_x_grid, max_x_grid, min_y_grid, max_y_grid])
                if enveloppe:
                    attribute_values.extend([min_x_poly, max_x_poly, min_y_poly, max_y_poly])
                new_feat.setAttributes(attribute_values)
                dp_grille.addFeatures([new_feat])        # ajoute les geometries et valeurs des enregistrements
                dp_grille.updateExtents()                # quitte le mode edition et enregistre les modifs

grille.commitChanges()

iface.mapCanvas().refresh()
#QMessageBox.information(None,"DEBUGn: " , "texte")

