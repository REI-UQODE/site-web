class FilMastodon{
    #balise;
    #usr_tag;
    #usr_id;
    #domaine;

    #est_horizontal;
    #etat_charger_publications = false;

    #fil_balise;
    #derniere_publication_chargee;
    #a_tout_charge = false;
    #pubs_charges = 0;

    static #PUBS_CHARGER_LIMITE = 5;

    constructor(balise){
        this.#balise = balise;
        this.#est_horizontal = balise.getAttribute("est_horizontal") === "true";

        if(!balise.getAttribute("usr").match(/@[a-z0-9_\.\-]+@[a-z0-9_\.\-]+/)){
            throw Error("Le nom d'utilisateur est invalide.");
        }
        [ , this.#usr_tag, this.#domaine] = balise.getAttribute("usr").split('@');

        this.insererFil();
    }

    executerDefilement(evenement){
        // Nombre de publications avant la fin du fil
        let pub_restantes;
        if(this.#est_horizontal){
            pub_restantes = Math.floor((1 - (this.#fil_balise.scrollLeft + this.#fil_balise.offsetWidth)/this.#fil_balise.scrollWidth) * this.#pubs_charges);
        }else{
            pub_restantes = Math.floor((1 - (this.#fil_balise.scrollTop + this.#fil_balise.offsetHeight)/this.#fil_balise.scrollHeight) * this.#pubs_charges);
        }

        if(pub_restantes <= 2){
            console.log("charger plus");
            this.chargerPublications();
        }
    }

    async insererFil(){        
        this.#balise.innerHTML = await fetch("/modules/mastodon/conteneur.html").then((e)=>{return e.text();});

        let compte = await fetch("https://"+this.#domaine+"/api/v1/accounts/lookup?acct="+this.#usr_tag).then((e)=>{return e.json()});
        this.#usr_id = compte.id;

        let header = this.#balise.getElementsByTagName("header")[0];
        header.innerHTML = 
            "<img src='"+compte.avatar+"' alt='"+compte.avatar_description+"'/>"+
            "<div>"+
                "<h3>"+compte.display_name+"</h3>"+
                "<p>Publications Mastodon de <a href='https://"+this.#domaine+"/"+this.#usr_tag+"'/>@"+this.#usr_tag+"@"+this.#domaine+"</a></p>"+
            "</div>";
        
        let publications = await fetch("https://"+this.#domaine+"/api/v1/accounts/"+compte.id+"/statuses?exclude_replies=true&limit="+FilMastodon.#PUBS_CHARGER_LIMITE).then((e)=>{return e.json();});

        this.#fil_balise = this.#balise.getElementsByTagName("fil")[0];
        this.#fil_balise.innerHTML = "";
        this.#fil_balise.addEventListener("scroll",(e)=>{this.executerDefilement(e)});
        for(let p of publications){
            this.ajouterPublication(this.#fil_balise,p);
            this.#derniere_publication_chargee = p.id;
        }
    }

    async chargerPublications(){
        if(this.#etat_charger_publications){
            return
        }
        this.#etat_charger_publications = true;

        if(this.#a_tout_charge){
            return;
        }

        let publications = await fetch("https://"+this.#domaine+"/api/v1/accounts/"+this.#usr_id+"/statuses?exclude_replies=true&max_id="+this.#derniere_publication_chargee+"&limit="+FilMastodon.#PUBS_CHARGER_LIMITE).then((e)=>{return e.json();});
        if(publications.length == 0){
            this.#a_tout_charge = true;
            return;
        }

        for(let p of publications){
            this.ajouterPublication(this.#fil_balise, p);
            this.#derniere_publication_chargee = p.id;
        }
        this.#etat_charger_publications = false;
    }

    ajouterPublication(balise, pub){
        let pubEl = document.createElement("div");
        
        let imagesConteneur = document.createElement("div");
        imagesConteneur.classList.add("publication-img-conteneur");
        for(let img of pub.media_attachments){
            if(!img.type == "image"){
                continue;
            }
            let image = document.createElement("img");
            image.src = img.url;
            image.alt = img.description;
            imagesConteneur.appendChild(image);
        }
        pubEl.appendChild(imagesConteneur);
        pubEl.innerHTML += "<a class='bouton' href='"+pub.url+"'>Ouvrir sur <img src='/images/mastodon-logo-white.svg'/> &gt;</a><div class='publication-description'>"+pub.content+"</div><p class='publication-date'><i>"+new Date(Date.parse(pub.created_at)).toLocaleString("fr-CA")+"</i></p>";
        balise.appendChild(pubEl);

        this.#pubs_charges++;
    }
}

document.addEventListener("DOMContentLoaded", async ()=>{
    let style = document.createElement("link");
    style.rel="stylesheet";
    style.type="text/css";
    style.href="/modules/mastodon/mastodon.css";
    document.getElementsByTagName("head")[0].appendChild(style);
    for(let e of document.getElementsByTagName("mastodon")){
        new FilMastodon(e);
    }
});