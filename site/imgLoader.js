/*---------------------------------------*
 * imgLoader.js							 *
 *										 *
 * Load les images selon leur catégorie. *
 *---------------------------------------*/


document.addEventListener('keydown', function(event)
{
    if (event.key === 'Escape')
    {closeModal();}
});


function loadImg (element, categorie)
{
	modal = document.getElementById("fond-modale");
	viewer = document.getElementById("image-modale");
	
	//Chargement du fichier JSON contenant la liste des images:
	//TODO: charger ça une seule fois au début au lieu d'à chaque clic!
	//TODO: handler les controles!
	fetch('imgs.json')
    .then(response => response.json())
    .then(data => {
        const cat = data.categories.find(cat => cat.categorie === categorie);
        if (cat)
        {
            const fichiers = cat.images.map(img => img.fichier);
            const noms = cat.images.map(img => img.nom);

            modal.style.display = "flex";
            viewer.innerHTML = `<img class="image-modale" src="images/${fichiers[0]}" alt="${noms[0]}">`;
        }
    })
    .catch(error => console.error("Erreur:", error));
}


function closeModal ()
{
	document.getElementById("fond-modale");
	modal.style.display = "none";
}