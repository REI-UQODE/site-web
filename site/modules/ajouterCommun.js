export async function ajouterBasDePage(){
    // Ajouter la feuille css
    let head = document.getElementsByTagName("head")[0];
    let css = document.createElement("link");
    css.rel = "stylesheet";
    css.type = "text/css";
    css.href = "/modules/bas-de-page.css";
    head.appendChild(css);

    let balise = document.getElementsByTagName("footer")[0];
    let html = "";
    await fetch("/modules/basDePage.html").then(r => r.text()).then(r => html=r);
    balise.innerHTML = html;
}

export async function ajouterBarreNav(){
    // Ajouter la feuille css
    let head = document.getElementsByTagName("head")[0];
    let css = document.createElement("link");
    css.rel = "stylesheet";
    css.type = "text/css";
    css.href = "/modules/barre-nav.css";
    head.appendChild(css);

    let balise = document.getElementsByTagName("nav")[0];
    let html = "";
    await fetch("/modules/barreNav.html").then(r => r.text()).then(r => html=r);
    balise.innerHTML = html;
}