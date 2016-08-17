##Vecteur=group
##couche_de_couverture_v162=name
##couche_de_polygones=vector
##champ_de_tri=field couche_de_polygones
##largeur_d_une_dalle=number 7000.0
##hauteur_d_une_dalle=number 6000.0
##pourcentage_autour_de_l_objet=number 0
##emprise_de_la_dalle=boolean False
##emprise_de_l_objet=boolean False
##sans_dalle_blanche=boolean False
##pas_de_decalage_pour_chercher_un_minimum_de_dalles=number 0
##couche_de_couverture=output vector

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
- 'row_poly_tile' la ligne de la dalle pour chaque 'id_poly'
- 'col_poly_tile' la colonne de la dalle pour chaque 'id_poly'
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
- 'id_poly' = attribute( $atlasfeature, 'id_poly' )
ou e version de QGIS >= 14
- 'id_poly' = attribute( @atlasfeature, 'id_poly' )

Pour une future i18n :
    'La taille de la dalle n\'est pas suffisante, essaie encore'
->    'Tiles\' dimensions are too small, try again!'

    'Vous avez choisi {} comme pourcentage de tampon. Le maximum est {}... Pourquoi ne pas essayer environ {} la prochaine fois ?'
->    'You choose {}. for overlap percentage. Maximum is {}... Why not try something around {} next time ?'

    'Vous avez choisi une valeur trop petite de pas de decalage pour reduire le nombre de dalles. Le minimum est {}. Pourquoi ne pas essayer environ {} la prochaine fois ?'
->    'You choose a too small value for pas_de_decalage_pour_chercher_un_minimum_de_dalles. Minimum is {}. Why not try something around {} next time ? '

    'You did not choose a polygon layer...'
->    'Vous n\'avez pas selectionne une couche de polygones...'

    'Le champ {} existe deja, modifier le code du script ou la table'
->    'Column {} is in original table, you must change either script or table'

Versions :
- V1.b du 27 mai 2016 version python ogr osvy
- V1.1 du 27 mai 2016 version processing jean-christophe.baudin@onema.fr
- V1.2 du 29 mai 2016
- V1.3 du 31 mai 2016
- V1.4 du 31 mai 2016 changement complet du traitement des optimisations
- V1.5 du 3 juin 2016 utilisation de l'exception recommandee GeoAlgorithmExecutionException(),
                      quelques variables renommees,
                      une chaine de tri ajoutee en sortie
- V1.5.1 du 3 juin 2016 renommage de variables
- V1.5.2 du 18 juin 2016 numerotation des dalles en lignes et colonnes pour chaque polygone
- V1.6.0 du 19 juin 2016 possibilite d'enregistrer la couche produite sur disque,
                        renommage de variables en vue version anglaise,
                        verifie que la couche en entree est une couche de polygones
- V1.6.1 du 20 juin 2016 modifications mineures pour etudier le cas ou la couche en entree n'a aucun attribut
- V1.6.2 du 25 juin 2016 utilisation de format() pour les sorties

Note :
    avec une version recente de qgis/processing il faut remplacer en ligne 4 
        ##champ_de_tri=field couche_de_polygones
    par
        ##champ_de_tri=optional field couche_de_polygones
"""


from qgis.core import *
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.tools.vector import VectorWriter
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from processing import *
from math import ceil


# limite du nombre maximum de deplacements
HALF_MAX_GAP = 150 # plus de 12 millions de calculs pour les 153 communes du Var pour en moyenne 4 dalles

# limite de pourcentage de taille du buffer
MAX_OVERLAP = 40

# fonction utile
center_of = lambda a, b : a + (b - a) / 2.0

# on renomme les variables
src_file = couche_de_polygones
ord_field = champ_de_tri
tile_dx = largeur_d_une_dalle
tile_dy = hauteur_d_une_dalle
overlap_percentage = pourcentage_autour_de_l_objet
tile_bound = emprise_de_la_dalle
poly_bound = emprise_de_l_objet
no_blank = sans_dalle_blanche
gap = pas_de_decalage_pour_chercher_un_minimum_de_dalles
output = couche_de_couverture

# pre-traitement des variables
# faut un minimum ;)
if tile_dx <= 1 or tile_dy <= 1:
    raise GeoAlgorithmExecutionException('La taille de la dalle n\'est pas suffisante, essaie encore')

# trop c'est trop !
if overlap_percentage > MAX_OVERLAP:
    raise GeoAlgorithmExecutionException('Vous avez choisi {} comme pourcentage de tampon. Le maximum est {}... Pourquoi ne pas essayer environ {} la prochaine fois ?'.format(overlap_percentage, MAX_OVERLAP, MAX_OVERLAP / 10))

# on ne garde que les dalles qui intersectent le polygone si on a defini un pas de decalage
if gap > 0:
    no_blank = True
    # plus de pb memoire mais ca va etre horriblement long
    if max(tile_dx, tile_dy) / gap > HALF_MAX_GAP:
        gap = int(ceil(max(tile_dx, tile_dy) / HALF_MAX_GAP))
        raise GeoAlgorithmExecutionException('Vous avez choisi une valeur trop petite de pas de decalage pour reduire le nombre de dalles. Le minimum est {}. Pourquoi ne pas essayer environ {} la prochaine fois ?'.format(gap, gap * 5))

# ouverture de la couche support d'entree
layer = processing.getObject(src_file)
provider = layer.dataProvider()
fields = provider.fields()
feats = processing.features(layer)
nb_feats = len(feats)
if layer.geometryType() <> 2:  # TODO polygons il faudrait trouver le fichier de constantes
    raise GeoAlgorithmExecutionException('Vous n\'avez pas selectionne une couche de polygones...')

# definition des attributs supplementaires
grid_fields = QgsFields()
additional_attributes = ('id_poly', 'id_tile', 'id_poly_tile', 'row_poly_tile', 'col_poly_tile')
additional_attributes_ord = ('ord_poly_tile',) if ord_field else ()
additional_attributes_tile_bound = ('min_x_tile', 'max_x_tile', 'min_y_tile', 'max_y_tile') if tile_bound else ()
additional_attributes_poly_bound = ('min_x_poly', 'max_x_poly', 'min_y_poly', 'max_y_poly') if poly_bound else ()
for f in fields:
    grid_fields.append(f)
    field_name = f.name()

    # en concurrence avec un attribut supplementaire
    if (field_name in additional_attributes) or \
       (field_name in additional_attributes_ord) or \
       (field_name in additional_attributes_tile_bound) or \
       (field_name in additional_attributes_poly_bound):
        raise GeoAlgorithmExecutionException('Le champ {} existe deja, modifier le code du script ou la table'.format(field_name))

# ajout des attributs supplementaires
for attr in additional_attributes:
    grid_fields.append(QgsField(attr, QVariant.Int))
for attr in additional_attributes_ord:
    grid_fields.append(QgsField(attr, QVariant.String))
for attr in additional_attributes_tile_bound:
    grid_fields.append(QgsField(attr, QVariant.Double))
for attr in additional_attributes_poly_bound:
    grid_fields.append(QgsField(attr, QVariant.Double))

# preparation de la couche grille
vw_grid = VectorWriter(output, None, grid_fields, provider.geometryType(), layer.crs())

id_poly = 0
id_tile = 0
# pour tous les polygones
for feature in feats:
    progress.setPercentage(int(100 * id_poly / nb_feats))

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
    poly_size_x = max_x_poly - min_x_poly
    poly_size_y = max_y_poly - min_y_poly
    tile_number_x = int(ceil(poly_size_x / tile_dx))
    tile_number_y = int(ceil(poly_size_y / tile_dy))
    center_x = center_of(min_x_poly, max_x_poly)
    center_y = center_of(min_y_poly, max_y_poly)
    minimum_x_center = center_x - tile_dx * tile_number_x / 2.0
    minimum_y_center = center_y - tile_dy * tile_number_y / 2.0
    margin_x = tile_number_x * tile_dx - poly_size_x
    margin_y = tile_number_y * tile_dy - poly_size_y

    # pour ne pas deplacer les dalles en dehors de l'emprise du polygone bufferise quand
    # on calculera la grille deplacee en limite
    shift_limit_x = lambda x : -margin_x / 2.0 if x < -margin_x / 2.0 else x if x < margin_x / 2.0 else margin_x / 2.0
    shift_limit_y = lambda y : -margin_y / 2.0 if y < -margin_y / 2.0 else y if y < margin_y / 2.0 else margin_y / 2.0

    # peut-on chercher a optimiser le nombre de dalles ?
    if tile_number_x * tile_number_y <= 2 or gap == 0: # pas d'optimisation possible ou desiree
        minimum_ajustment_x_step = 0
        minimum_ajustment_y_step = 0
    else:
        # on calcule le nombre de decalages possibles, arrondi superieur pour aller a la limite
        half_max_shift_number_x = int(ceil(margin_x / 2.0 / gap))
        half_max_shift_number_y = int(ceil(margin_y / 2.0 / gap))

        # nombre de case minimum intersectant le polygone
        minimum_tile_number = 0

        # on parcourt tous les decalages possibles
        for ajustment_x_step in range(-half_max_shift_number_x, half_max_shift_number_x + 1):
            for ajustment_y_step in range(-half_max_shift_number_y, half_max_shift_number_y + 1):
                intersect_number = 0

                # on cherche pour toutes les dalles si elles intersectent le polygone bufferise
                for tile_x in range(tile_number_x):
                    for tile_y in range(tile_number_y):
                        rectangle = QgsGeometry.fromRect( \
                                        QgsRectangle( \
                                            minimum_x_center + tile_x * tile_dx + shift_limit_x(ajustment_x_step * gap), \
                                            minimum_y_center + tile_y * tile_dy + shift_limit_y(ajustment_y_step * gap), \
                                            minimum_x_center + (tile_x + 1) * tile_dx + shift_limit_x(ajustment_x_step * gap), \
                                            minimum_y_center + (tile_y + 1) * tile_dy + shift_limit_y(ajustment_y_step * gap)))

                        # l'intersection se fait avec le polygone bufferise
                        if rectangle.intersects(buffer_geom):
                            intersect_number += 1

                # on conserve la premiere valeur minimale proche de la moyenne en distance
                if intersect_number < minimum_tile_number or minimum_tile_number == 0:
                    balance = (ajustment_x_step - half_max_shift_number_x)**2 + (ajustment_y_step - half_max_shift_number_y)**2
                    minimum_tile_number = intersect_number
                    minimum_ajustment_x_step = ajustment_x_step
                    minimum_ajustment_y_step = ajustment_y_step
                    minimum_balance = balance
                elif intersect_number == minimum_tile_number:
                    balance = (ajustment_x_step - half_max_shift_number_x)**2 + (ajustment_y_step - half_max_shift_number_y)**2
                    if balance < minimum_balance:
                        minimum_tile_number = intersect_number
                        minimum_ajustment_x_step = ajustment_x_step
                        minimum_ajustment_y_step = ajustment_y_step
                        minimum_balance = balance

    # on a determine la position des dalles, on peut maintenant creer la grille pour ce polygone
    id_poly += 1
    id_poly_tile = 0
    row_poly_tile = 0
    for tile_x in range(tile_number_x):
        row_poly_tile += 1
        col_poly_tile = 0
        for tile_y in range(tile_number_y):
            col_poly_tile += 1

            # on recalcule la dalle
            min_x_tile = minimum_x_center + tile_x * tile_dx + shift_limit_x(minimum_ajustment_x_step * gap)
            min_y_tile = minimum_y_center + tile_y * tile_dy + shift_limit_y(minimum_ajustment_y_step * gap)
            max_x_tile = minimum_x_center + (tile_x + 1) * tile_dx + shift_limit_x(minimum_ajustment_x_step * gap)
            max_y_tile = minimum_y_center + (tile_y + 1) * tile_dy + shift_limit_y(minimum_ajustment_y_step * gap)
            rectangle = QgsGeometry.fromRect(QgsRectangle(min_x_tile, min_y_tile, max_x_tile, max_y_tile))

            # l'intersection se fait avec le polygone bufferise
            if not no_blank or (no_blank and rectangle.intersects(buffer_geom)):
                id_tile += 1
                id_poly_tile += 1
                new_feat = QgsFeature()
                new_feat.setGeometry(rectangle)
                # attributs standards
                attribute_values = feature.attributes()[:]                                              
                # attributs supplementaires
                attribute_values.extend([id_poly, id_tile, id_poly_tile, row_poly_tile, col_poly_tile]) 
                # attribut supplementaire pour tri
                if ord_field:
                    attribute_values.append('{}#{:04d}'.format(feature[ord_field], id_poly_tile))     
                # attributs supplementaires coord dalle
                if tile_bound:
                    attribute_values.extend([min_x_tile, max_x_tile, min_y_tile, max_y_tile])           
                # attributs supplementaires coord enveloppe
                if poly_bound:
                    attribute_values.extend([min_x_poly, max_x_poly, min_y_poly, max_y_poly])           

                # ajoute les geometries et valeurs des enregistrements
                new_feat.setAttributes(attribute_values)
                vw_grid.addFeature(new_feat)
del vw_grid

# pour memoire :
#QMessageBox.information(None, 'DEBUGn: ' , 'texte') # pas recommande !
#progress.setInfo('texte')
#progress.setText('texte')
#raise GeoAlgorithmExecutionException('texte')
