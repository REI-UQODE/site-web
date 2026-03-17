export async function ajouterBasDePage(){
    // Ajouter la feuille css
    let head = document.getElementsByTagNameNS("head")[0];
    let css = document.createElement("link");
    css.rel = "stylesheet";
    css.type = "text/css";
    css.href = "/footer.css";
    head.appendChild(css);

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