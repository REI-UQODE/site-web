export async function ajouterBasDePage(){
    let balise = document.getElementsByTagName("footer")[0];
    let html = "";
    await fetch("basDePage.html").then(r => r.text()).then(r => html=r);
    balise.innerHTML = html;
}

export async function ajouterBarreNav(){
    let balise = document.getElementsByTagName("nav")[0];
    let html = "";
    await fetch("barreNav.html").then(r => r.text()).then(r => html=r);
    balise.innerHTML = html;
}