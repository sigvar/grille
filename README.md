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
