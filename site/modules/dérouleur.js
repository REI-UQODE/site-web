document.addEventListener("DOMContentLoaded", async ()=>{
    let head = document.getElementsByTagName("head")[0];
    let css = document.createElement("link");
    css.rel = "stylesheet";
    css.type = "text/css";
    css.href = "/modules/dérouleur.css";
    head.appendChild(css);

    for(let e of document.getElementsByTagName("derouleur")){
        bouton = document.createElement("button");
        if(e.getAttribute("actif") === "true"){
            bouton.innerText = "-"
        }else{
            bouton.innerText = "+"
        }
        let conteneur = document.createElement("div")
        conteneur.innerHTML = e.innerHTML;
        if (e.getAttribute("actif") !== "true"){
            conteneur.classList.add("caché")
        }
        e.innerHTML = "";
        e.appendChild(bouton);
        e.appendChild(conteneur);

        bouton.addEventListener("click", ()=>{
            if (e.getAttribute("actif") === "false"){
                e.setAttribute("actif","true");
                bouton.innerText="-";
                conteneur.classList.remove("caché");
            } else {
                e.setAttribute("actif","false");
                bouton.innerText="+";
                conteneur.classList.add("caché");
            }
        })
    }
})