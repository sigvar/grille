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
