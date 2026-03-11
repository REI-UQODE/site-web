/*---------------------------------------*
 * imgLoader.js							 *
 *										 *
 * Load les images selon leur catégorie. *
 *---------------------------------------*/


categories = []; //liste des images (classées par catégories) obtenue du JSON
categorieActive = -1; //catégorie présentement à l'écran
numImg = -1; //image actuellement à l'écran

modal = document.getElementById("fond-modale");
viewer = document.getElementById("image-modale");
titre = document.getElementById("titre-modale");

document.addEventListener('keydown', function(event)
{
    if (event.key === 'Escape')
    {closeModal();}
    else if (event.key === 'ArrowRight' && numImg >= 0)
    {nextImg();}
    else if (event.key === 'ArrowLeft' && numImg >= 0)
    {prevImg();}
});


async function loadImg (categorieDemandee)
{
	//Chargement du fichier JSON contenant la liste des images:
	if (categories.length === 0)
	{
		await fetch('imgs.json')
		.then(response => response.json())
		.then(data => {categories = data.categories;})
		.catch(error => console.error("Impossible d'accéder à la liste des images: ", error));
    }
	
	//Sélection de la bonne catégorie:
	for (i = 0; i < categories.length; i++)
	{
		if (categories[i].categorie === categorieDemandee)
		{categorieActive = i;}
	}
	if (categorieActive === -1)
	{console.error("Erreur: Cette catégorie n'existe pas."); return;}
	numImg = 0;
	
	//Affichage:
	modal.style.display = "flex";
	viewer.innerHTML = `<img class="image-modale" src="images/${categories[categorieActive].images[numImg].fichier}" alt="${categories[categorieActive].images[numImg].nom}">`;
	titre.innerHTML = categories[categorieActive].images[numImg].nom;
}


function prevImg ()
{
	if (numImg === 0)
	{numImg = categories[categorieActive].images.length - 1;}
	else
	{numImg--;}
	viewer.innerHTML = `<img class="image-modale" src="images/${categories[categorieActive].images[numImg].fichier}" alt="${categories[categorieActive].images[numImg].nom}">`;
	titre.innerHTML = categories[categorieActive].images[numImg].nom;
}


function nextImg ()
{
	if (numImg === categories[categorieActive].images.length - 1)
	{numImg = 0;}
	else
	{numImg++;}
	viewer.innerHTML = `<img class="image-modale" src="images/${categories[categorieActive].images[numImg].fichier}" alt="${categories[categorieActive].images[numImg].nom}">`;
	titre.innerHTML = categories[categorieActive].images[numImg].nom;
}


function closeModal ()
{
	document.getElementById("fond-modale");
	modal.style.display = "none";
	categorieActive = -1;
	numImg = -1;
}