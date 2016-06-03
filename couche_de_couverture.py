##Vector=group
##couche_de_couverture=name
##couche_de_polygones=vector
##champ_de_tri=field couche_de_polygones
##largeur_d_une_dalle=number 7000.0
##hauteur_d_une_dalle=number 6000.0
##pourcentage_autour_de_l_objet=number 0
##emprise_de_la_dalle=boolean False
##emprise_de_l_objet=boolean False
##sans_dalle_blanche=boolean False
##pas_de_decalage_pour_chercher_un_minimum_de_dalles=number 0
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
- une colonne de la couche a partir de laquelle on composera une colonne permettant un tri dans l'atlas,
     la valeur de cette colonne sera completee du caractere # et de l'ordre de la dalle sous la forme 000n
     (4 chiffres, en completant par des 0 a gauche si besoin)
- la taille d'une dalle,
- un pourcentage de recouvrement autour du polygone
- si on souhaite les coordonnees de chaques dalles,
- si on souhaite les coordonnees de l'enveloppe de l'objet d'origine,
- si on ne conserve que les cases sans intersection avec le polygone,
- et quand on indique un pas de decalage, l'algorithme cherche a minimiser le nombre de cases par polygones
     en deplacant les cases par des pas de cette valeur, il ne conserve que les cases sans intersection
     avec le polygone.
     La taille du pas est limitee au trois-centieme de la taille d'une dalle et ca peut etre TRES lent.

Comme les colonnes de la table d'origine sont reprises et que des colonnes sont ajoutees, en cas de conflit de nom
le script s'arrete.

La couche de sortie en plus des attributs conserves presente 4 attributs supplementaires :
- 'id_poly'       un entier pour chaque objet d'origine
- 'id_tile'       un entier unique par dalle
- 'id_poly_tile'  un entier unique par dalle pour chaque 'id_poly'
- 'ord_poly_tile' une valeur de tri composee du champ choisi et de l'entier unique par dalle pour chaque 'id_poly'

Et si on a demande les coordonnees de la dalle :
- 'min_x_tile'    un double pour la valeur x min
- 'max_x_tile'    un double pour la valeur x max
- 'min_y_tile'    un double pour la valeur y min
- 'max_y_tile'    un double pour la valeur y max

Et si on a demande les coordonnees de l'enveloppe de l'objet d'origine :
- 'min_x_poly'    un double pour la valeur x min
- 'max_x_poly'    un double pour la valeur x max
- 'min_y_poly'    un double pour la valeur y min
- 'max_y_poly'    un double pour la valeur y max

On peut filtrer l'affichage de la grille quand un composeur est actif en utilisant dans le style une regle comme :
- "id_poly" = attribute( $atlasfeature, 'id_poly' )
ou e version de QGIS >= 14
- "id_poly" = attribute( @atlasfeature, 'id_poly' )

Versions :
- V1.b du 27 mai 2016 osvy
- V1.1 du 27 mai 2016 jean-christophe.baudin@onema.fr
- V1.2 du 29 mai 2016
- V1.3 du 31 mai 2016
- V1.4 du 31 mai 2016 changement complet du traitement des optimisations
- V1.5 du 3 juin 2016 utilisation de l'exception recommandee GeoAlgorithmExecutionException(),
                      quelques variables renommees,
                      une chaine de tri ajoutee en sortie
- V1.5.1 du 3 juin 2016 renommage de variables
"""
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from processing import *
from math import ceil

# limite du nombre maximum de deplacements
DEMI_MAX_DEPLACEMENT = 150 # plus de 12 millions de calculs pour les 153 communes du Var pour en moyenne 4 dalles
# limite de pourcentage de taille du buffer
MAX_OVERLAP = 40

# fonction utile
milieu = lambda a, b : a + (b - a) / 2.0

#on renomme les variables
src_file = couche_de_polygones
ord_field = champ_de_tri
tile_dx = largeur_d_une_dalle
tile_dy = hauteur_d_une_dalle
overlap_percentage = pourcentage_autour_de_l_objet
tile_bound = emprise_de_la_dalle
object_bound = emprise_de_l_objet
no_blank = sans_dalle_blanche
gap = pas_de_decalage_pour_chercher_un_minimum_de_dalles

# pre-traitement des variables
# faut un minimum ;)
if tile_dx <= 1 or tile_dy <= 1:
    raise GeoAlgorithmExecutionException('la taille de la dalle n\'est pas suffisante')

# trop c'est trop !
if overlap_percentage > MAX_OVERLAP:
    raise GeoAlgorithmExecutionException("Information: You choose %s. for overlap percentage. Maximum is %s ... Why not try something around %s next time ? "%(overlap_percentage, MAX_OVERLAP, MAX_OVERLAP / 10))

# on ne garde que les dalles qui intersectent le polygone si on a defini un pas de decalage
if gap > 0:
    no_blank = True
    # plus de pb memoire mais ca va etre horriblement long
    if max(tile_dx, tile_dy) / gap > DEMI_MAX_DEPLACEMENT:
        gap = int(ceil(max(tile_dx, tile_dy) / DEMI_MAX_DEPLACEMENT)) * 5
        raise GeoAlgorithmExecutionException("You choose a too small value for pas_de_decalage_pour_chercher_un_minimum_de_dalles. Why not try something around %s next time ? "%gap)

# ouverture de la couche support d'entree
layer = processing.getObject(src_file)
provider = layer.dataProvider()
fields = provider.fields()
feats = processing.features(layer)
nb_feat = len(feats)

# preparation de la couche grille
grille = QgsVectorLayer("Polygon", "couche_de_couverture_de_"+ str(layer.name()), "memory")
QgsMapLayerRegistry.instance().addMapLayer(grille)
dp_grille = grille.dataProvider()

# definition des attributs supplementaires
attributs_sup = ('id_poly', 'id_tile', 'id_poly_tile')
attributs_sup_tri = ('ord_poly_tile',)
attributs_sup_grid = ('min_x_tile', 'max_x_tile', 'min_y_tile', 'max_y_tile', )
attributs_sup_env = ('min_x_poly', 'max_x_poly', 'min_y_poly', 'max_y_poly', )
for f in fields:
    dp_grille.addAttributes([f])
    field_name = f.name()
    # en concurrence avec un attribut supplementaire
    if (field_name in attributs_sup) or (field_name in attributs_sup_tri) or \
        (tile_bound and field_name in attributs_sup_grid) or \
        (object_bound and field_name in attributs_sup_env):
        raise GeoAlgorithmExecutionException('le champ %s existe deja, modifier le code du script ou la table '%field_name)
# ajout des attributs supplementaires standards
for attr in attributs_sup:
    dp_grille.addAttributes([QgsField(attr, QVariant.Int)])
for attr in attributs_sup_tri:
    dp_grille.addAttributes([QgsField(attr, QVariant.String)])
# ajout des attributs supplementaires de coordonnees de la dalle
if tile_bound:
    for attr in attributs_sup_grid:
        dp_grille.addAttributes([QgsField(attr, QVariant.Double)])
# ajout des attributs supplementaires de coordonnees de l'enveloppe du polygone (bufferise) support
if object_bound:
    for attr in attributs_sup_env:
        dp_grille.addAttributes([QgsField(attr, QVariant.Double)])

id_poly = 0
id_tile = 0
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
        buffer_geom = feature.geometry().buffer(overlap_percentage / 100.0 * max((max_x_poly - min_x_poly), (max_y_poly - min_y_poly)), 10)
        bounding_geom = buffer_geom.boundingBox()
        min_x_poly = bounding_geom.xMinimum()
        max_x_poly = bounding_geom.xMaximum()
        min_y_poly = bounding_geom.yMinimum()
        max_y_poly = bounding_geom.yMaximum()

    # dimensions des cases/dalles
    taille_poly_x = max_x_poly - min_x_poly
    taille_poly_y = max_y_poly - min_y_poly
    nombre_case_x = int(ceil(taille_poly_x / tile_dx))
    nombre_case_y = int(ceil(taille_poly_y / tile_dy))
    milieu_x = milieu(min_x_poly, max_x_poly)
    milieu_y = milieu(min_y_poly, max_y_poly)
    minimum_x_centre = milieu_x - tile_dx * nombre_case_x / 2.0
    minimum_y_centre = milieu_y - tile_dy * nombre_case_y / 2.0
    marge_x = nombre_case_x * tile_dx - taille_poly_x
    marge_y = nombre_case_y * tile_dy - taille_poly_y

    # pour ne pas deplacer les dalles en dehors de l'emprise du polygone bufferise quand
    # on calculera la grille deplacee en limite
    limite_decalage_x = lambda x : -marge_x / 2.0 if x < -marge_x / 2.0 else x if x < marge_x / 2.0 else marge_x / 2.0
    limite_decalage_y = lambda y : -marge_y / 2.0 if y < -marge_y / 2.0 else y if y < marge_y / 2.0 else marge_y / 2.0

    # peut-on chercher a optimiser le nombre de dalles ?
    if nombre_case_x * nombre_case_y <= 2 or gap == 0: # pas d'optimisation possible ou desiree
        minimum_ajustement_x_pas = 0
        minimum_ajustement_y_pas = 0
    else:
        # on calcule le nombre de decalages possibles, arrondi superieur pour aller a la limite
        demi_nombre_essais_decalage_x = int(ceil(marge_x / 2.0 / gap))
        demi_nombre_essais_decalage_y = int(ceil(marge_y / 2.0 / gap))
        # nombre de case minimum intersectant le polygone
        minimum_case = 0
        # on parcourt tous les decalages possibles
        for ajustement_x_pas in range(-demi_nombre_essais_decalage_x, demi_nombre_essais_decalage_x + 1):
            for ajustement_y_pas in range(-demi_nombre_essais_decalage_y, demi_nombre_essais_decalage_y + 1):
                nombre_intersection = 0
                # on cherche pour toutes les dalles si elles intersectent le polygone bufferise
                for case_x in range(nombre_case_x):
                    for case_y in range(nombre_case_y):
                        rectangle = QgsGeometry.fromRect( \
                                        QgsRectangle( \
                                            minimum_x_centre + case_x * tile_dx + limite_decalage_x(ajustement_x_pas * gap), \
                                            minimum_y_centre + case_y * tile_dy + limite_decalage_y(ajustement_y_pas * gap), \
                                            minimum_x_centre + (case_x + 1) * tile_dx + limite_decalage_x(ajustement_x_pas * gap), \
                                            minimum_y_centre + (case_y + 1) * tile_dy + limite_decalage_y(ajustement_y_pas * gap)))
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
    id_poly_tile = 0
    for case_x in range(nombre_case_x):
        for case_y in range(nombre_case_y):
            # on recalcule la dalle
            min_x_tile = minimum_x_centre + case_x * tile_dx + limite_decalage_x(minimum_ajustement_x_pas * gap)
            min_y_tile = minimum_y_centre + case_y * tile_dy + limite_decalage_y(minimum_ajustement_y_pas * gap)
            max_x_tile = minimum_x_centre + (case_x + 1) * tile_dx + limite_decalage_x(minimum_ajustement_x_pas * gap)
            max_y_tile = minimum_y_centre + (case_y + 1) * tile_dy + limite_decalage_y(minimum_ajustement_y_pas * gap)
            rectangle = QgsGeometry.fromRect(QgsRectangle( min_x_tile, min_y_tile, max_x_tile, max_y_tile))
            # l'intersection se fait avec le polygone bufferise
            if not no_blank or (no_blank and rectangle.intersects(buffer_geom)):
                id_tile += 1
                id_poly_tile += 1
                new_feat = QgsFeature()
                new_feat.setGeometry(rectangle)
                attribute_values = feature.attributes()[:]                                             # attributs standards
                attribute_values.extend([id_poly, id_tile, id_poly_tile])                              # attributs supplementaires
                attribute_values.append("%s#%s"%(feature[ord_field], ("0000%s"%id_poly_tile)[-4:]))    # attribut supplementaire pour tri
                if tile_bound:
                    attribute_values.extend([min_x_tile, max_x_tile, min_y_tile, max_y_tile])          # attributs supplementaires coord dalle
                if object_bound:
                    attribute_values.extend([min_x_poly, max_x_poly, min_y_poly, max_y_poly])          # attributs supplementaires coord enveloppe
                new_feat.setAttributes(attribute_values)
                dp_grille.addFeatures([new_feat])        # ajoute les geometries et valeurs des enregistrements
                dp_grille.updateExtents()                # quitte le mode edition et enregistre les modifs

grille.commitChanges()

iface.mapCanvas().refresh()

# pour memoire :
#QMessageBox.information(None,"DEBUGn: " , "texte") # pas recommande !
#progress.setInfo('texte')
#raise GeoAlgorithmExecutionException('texte')
#progress.setText(text)
