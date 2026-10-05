import base64
import cgi
import datetime
import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

"""
"hash":{
    "soumissionaire":"nom",
    "nom_bot":"botv1",
    "hash":"hash",
    "date":"date",
    "rep":"répertoire"
    "score":1000
} 
"""
soumissions = {}
soumissions_ordonnees = []
"""
"soumissionaire":[scores]
"""
scores = {}
jeton_admin : str

class defiServeur(BaseHTTPRequestHandler):
    def send_error(self, code : int, message : str|None = None, explain : str|None = None):
        message_json = {}
        if message:
            message_json["message"] = message
        if explain:
            message_json["explain"] = explain
        fichier = json.dumps(message_json).encode("utf8")

        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",len(fichier))
        self.send_header("Access-Control-Allow-Origin",'*')
        self.end_headers()
        self.wfile.write(fichier)

    def trier_soumissions_dates(liste : list[dict[str]]):
        """Trie les soumissions selon la date
        """
        # Tri par base O(n)

        # Formatter la liste.
        # (UNIX Timestamp, soumission)
        liste_dict = {}
        timestamps = [0]*len(liste)
        for i in range(len(liste)):
            t = datetime.datetime.strptime(liste[i]["date"], "%Y-%m-%d %H:%M:%S").timestamp()
            liste_dict[t] = liste[i]
            timestamps[i] = [t,0]
        
        n_items : list[int] = [0,0,0,0,0,0,0,0,0,0]
        somme : list[int] = [0,0,0,0,0,0,0,0,0,0]
        dec : int = 0
        tout_zero = False
        while(True):
            # Effacer les listes de travail
            for i in range(10):
                n_items[i] = 0
                somme[i] = 0
            # Assigner la position à l'intérieur de la classe
            tout_zero = True
            for t in timestamps:
                d = int((t[0] // (10**dec)) % 10)
                t[1] = n_items[d]
                n_items[d] += 1
                if d != 0:
                    tout_zero = False
            if tout_zero:
                break # La liste est triée
            # Trouver la position de la classe
            somme[0] = 0
            for i in range(len(n_items) - 1):
                somme[i+1] = somme[i] + n_items[i]
            # Ordonner les éléments selon leur position absolue, sur place
            j : int = 0
            tmp : list[int,int]
            for i in range(len(timestamps)):
                d = int((timestamps[i][0] // (10**dec)) % 10)
                j = timestamps[i][1] + somme[d]
                while j != i:
                    tmp = timestamps[i]
                    timestamps[i] = timestamps[j]
                    timestamps[j] = tmp
                    d = int((timestamps[i][0] // (10**dec)) % 10)
                    j = timestamps[i][1] + somme[d]
            dec += 1

        # Replacer les éléments
        for i in range(len(timestamps)):
            liste[i] = liste_dict[timestamps[i][0]]

    def recalculer_scores():
        scores = {}
        
        defiServeur.trier_soumissions_dates(soumissions_ordonnees)
        for s in soumissions_ordonnees:
            if s["soumissionaire"] not in scores:
                scores[s["soumissionaire"]] = [s["score"]]
            if s["score"] > scores[s["soumissionaire"]][-1]:
                scores[s["soumissionaire"]].append(s["score"])
            
    def do_PATCH(self):
        global jeton_admin

        self.params = {}
        if '?' in self.path:
            url = self.path.split('?')
            self.path = url[0]
            for p in url[1].split('&'):
                self.params[p.split('=')[0]] = p.split('=')[1]
        
        if re.match(r"^/effacer/soumission/[a-zA-Z0-9_\-#]+$", self.path):
            if "Authorization" not in self.headers:
                self.send_error(401, "Veuillez vous authentifier.")
                return
            if self.headers["Authorization"] != f"Token {jeton_admin}":
                self.send_error(403, "Vous n'êtes pas autorisé à accéder à cette ressource.")
                return

            hash = self.path.split('/')[-1]
            if hash not in soumissions:
                self.send_error(404, "La soumission n'existe pas.")
                return
            
            shutil.rmtree(soumissions[hash]["rep"])
            if len(os.listdir("./" + soumissions[hash]["soumissionaire"].replace(' ','_'))) == 0:
                os.rmdir("./" + soumissions[hash]["soumissionaire"].replace(' ','_'))
            soumissions_ordonnees.remove(soumissions.pop(hash))
            threading.Thread(target=defiServeur.recalculer_scores).start() # Pas thread-safe

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin",'*')
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            return
        if self.path == "/effacer/soumissions":
            if "Authorization" not in self.headers:
                self.send_error(401, "Veuillez vous authentifier.")
                return
            if self.headers["Authorization"] != f"Token {jeton_admin}":
                self.send_error(403, "Vous nêtes pas autorisé à accéder à cette ressource.")
                return

            if "Content-Type" not in self.headers or not re.match(r"application/json", self.headers["Content-Type"]):
                self.send_error(400, "Un JSON est requis")
                return
            if "Content-Length" not in self.headers:
                self.send_error(411, "L'en-tête 'Content-Length' est requis.")
                return
            
            try:
                message = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf8"))
            except Exception as e:
                self.send_error(400, "Le contenu du message n'a pas pus être lu.")
                return

            if not isinstance(message, list):
                self.send_error(400, "Le message doit être une liste de hashs")
                return
            
            hashs_retires = []
            for h in message:
                if h not in soumissions:
                    continue
                shutil.rmtree(soumissions[h]["rep"])
                if len(os.listdir("./" + soumissions[h]["soumissionaire"].replace(' ','_'))) == 0:
                    os.rmdir("./" + soumissions[h]["soumissionaire"].replace(' ','_'))
                soumissions_ordonnees.remove(soumissions.pop(h))
                hashs_retires.append(h)
            threading.Thread(target=defiServeur.recalculer_scores).start() # Pas thread-safe

            reponse = json.dumps(hashs_retires).encode("utf8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(reponse))
            self.send_header("Access-Control-Allow-Origin",'*')
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            self.wfile.write(reponse)
            return
        
        if re.match(r"^/effacer/soumissionaire/[a-zA-Z0-9\-_#]+$", self.path):
            if "Authorization" not in self.headers:
                self.send_error(401, "Veuillez vous authentifier.")
                return
            if self.headers["Authorization"] != f"Token {jeton_admin}":
                self.send_error(403, "Vous n'êtes pas autorisé à accéder à cette ressource.")
                return
            
            soumissionaire = base64.b64decode(self.path.split('/')[-1].replace('_','/').replace('-','+').replace('#','=').encode("utf8")).decode("utf8")
            hashs_retires = []
            for i in range(len(soumissions.items())):
                if soumissions_ordonnees[i]["soumissionaire"] == soumissionaire:
                    hashs_retires.append(i)
                if os.path.exists("./" + soumissionaire.replace(' ','_')):
                    shutil.rmtree("./" + soumissionaire.replace(' ','_'))
            for i in range(len(hashs_retires)):
                hashs_retires[i] = soumissions_ordonnees[hashs_retires[i]]["hash"]
                soumissions_ordonnees.remove(i)
                soumissions.pop(hashs_retires[i])
            
            if len(hashs_retires) == 0:
                self.send_error(404, "Aucun soumissionaire trouvé.")
                return
            
            reponse = json.dumps(hashs_retires).encode("utf8")

            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",len(reponse))
            self.send_header("Access-Control-Allow-Origin",'*')
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            self.wfile.write(reponse)
            return
        
        if self.path == "/effacer/soumissionaires":
            if "Authorization" not in self.headers:
                self.send_error(401, "Veuillez vous authentifier.")
                return
            if self.headers["Authorization"] != f"Token {jeton_admin}":
                self.send_error(403, "Vous n'êtes pas autorisé à accéder à cette ressource.")
                return

            if "Content-Type" not in self.headers or not re.match(r"application/json", self.headers["Content-Type"]):
                self.send_error(400, "Un JSON est requis")
                return
            if "Content-Length" not in self.headers:
                self.send_error(411, "L'en-tête 'Content-Length' est requis.")
                return
            
            try:
                message = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf8"))
            except:
                self.send_error(400, "Le contenu du message n'a pas pus être lu.")
                return

            if not isinstance(message, list):
                self.send_error(400, "Le message doit être une liste de hashs")
                return
            
            hashs_retires = []
            for s in message:
                for i in range(len(soumissions_ordonnees)):
                    if soumissions_ordonnees[i]["soumissionaire"] == s:
                        hashs_retires.append(i)
                if os.path.exists("./" + s.replace(' ','_')):
                    shutil.rmtree("./" + s.replace(' ','_'))
            for i in range(len(hashs_retires)):
                hashs_retires[i] = soumissions_ordonnees[hashs_retires[i]]["hash"]
                soumissions_ordonnees.pop(i)
                soumissions.pop(hashs_retires[i])
            threading.Thread(target=defiServeur.recalculer_scores).start() # Pas thread-safe

            reponse = json.dumps(hashs_retires).encode("utf8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", len(reponse))
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            self.wfile.write(reponse)
            return
        self.send_error(404, "URL invalide.")

    def do_POST(self):
        self.params = {}
        if '?' in self.path:
            url = self.path.split('?')
            self.path = url[0]
            for p in url[1].split('&'):
                self.params[p.split('=')[0]] = p.split('=')[1]

        if self.path == "/soumission":
            if "multipart/form-data" not in self.headers['Content-Type'].split(';'):
                self.send_error(400, "Veuillez fournir un formulaire mulipart")
                return
            
            try:
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"})
            except:
                self.send_error(400, "Le formulaire multipart n'a pas pus être lus")
                return

            if "soumissionaire" not in form:
                self.send_error(400, "Le 'soumissionaire' n'est pas spécifié")
                return
            if not isinstance(form["soumissionaire"].value, str):
                self.send_error(400, "Le 'soumissionaire' n'est pas un string")
                return
            if len(form["soumissionaire"].value) > 64:
                self.send_error(400, "Le 'hash' ne peut pas avoir une longueur supérieure à 64")
                return
            if "nom_bot" not in form:
                self.send_error(400, "Le 'nom_bot' n'est pas spécifié")
                return
            if not isinstance(form["nom_bot"].value, str):
                self.send_error(400, "Le 'nom_bot' n'est pas un string")
                return
            if len(form["nom_bot"].value) > 64:
                self.send_error(400, "Le 'nom_bot' ne peut pas avoir une longueur supérieure à 64")
                return
            if len(form["code_source"].value) > 512:
                self.send_error(400, "Le 'code_source' ne peut pas avoir une longueur supérieure à 512")
                return
            if "hash" not in form:
                self.send_error(400, "Le 'hash' n'est pas spécifié")
                return
            if not isinstance(form["hash"].value, str):
                self.send_error(400, "Le 'hash' n'est pas un string")
                return
            if re.match(r"[^a-zA-Z0-9_\-#]", form["hash"].value):
                self.send_error(400, "Le 'hash' ne peut contenir que des lettes, des chiffres et un de '_', '-', '#'")
                return
            if len(form["hash"].value) > 64:
                self.send_error(400, "Le 'hash' ne peut pas avoir une longueur supérieure à 64")
                return
            if "zip" not in form:
                self.send_error(400, "Le 'zip' n'est pas spécifié")
                return
            if not form["zip"].filename:
                self.send_error(400, "Le 'zip' n'est pas un fichier")
                return
            if not form["zip"].filename.endswith(".zip"):
                self.send_error(400, "Le 'zip' doit être un fichier .zip")
                return
            if form["hash"].value in soumissions:
                self.send_error(400, f"Le défi 'hash:({form["hash"]}) existe déjà'")
                return

            rep_base = "./" + base64.b64encode(form["soumissionaire"].value.encode("utf8")).decode("utf8").replace('/','_')
            rep = rep_base
            if not os.path.exists(rep):
                os.makedirs(rep)
            rep += '/' + form["hash"].value
            os.makedirs(rep)

            try:
                with open(rep + '/' + form["zip"].filename, "wb") as f:
                    f.write(form["zip"].file.read())
                rep_zip = rep + '/' + form["zip"].filename
            except:
                self.send_error(500, "Impossible d'enregistrer le fichier.")
                return
            
            if not zipfile.is_zipfile(rep_zip):
                shutil.rmtree(rep_base)
                self.send_error(400, "Le 'zip' est corrompu.")
                return
            
            fichier_zip = zipfile.ZipFile(rep_zip)
            if "lancer" not in fichier_zip.namelist():
                shutil.rmtree(rep_base)
                self.send_error(400, "Le 'zip' ne contient pas de fichier 'lancer'")
                return
            
            zipfile.ZipFile(rep_zip).extractall(rep)

            try:
                res = subprocess.run(["docker","run","--rm","-v",f"{rep}:/app","defis-oct2026"], check=False, capture_output=True, text=True).stdout
            except:
                shutil.rmtree(rep)
                self.send_error(500, "Le programme a rencontré une erreur.")
                return
            
            res_nombres = re.findall(r"[0-9]+", res)
            if len(res_nombres) == 0:
                shutil.rmtree(rep)
                self.send_error(500, "Le programme n'a pas répondu avec un nombre.")
                return
            score = int(res_nombres[-1])

            for i in range(2, int(score**0.5) + 1):
                if score % i == 0:
                    shutil.rmtree(rep)
                    self.send_error(500, "Le programme a répondu avec un nombre non-premier")
                    return
            
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            soumission = {
                "soumissionaire":form["soumissionaire"].value,
                "nom_bot":form["nom_bot"].value,
                "code_source":form["code_source"].value,
                "hash": form["hash"].value,
                "date": date,
                "rep": rep,
                "score": score
            }
            soumissions[form["hash"].value] = soumission
            soumissions_ordonnees.append(soumission)

            if form["soumissionaire"].value not in scores:
                scores[form["soumissionaire"].value] = [{"date":date, "score":score}]
            if score > scores[form["soumissionaire"].value][-1]["score"]:
                scores[form["soumissionaire"].value].append(score)

            fichier = json.dumps({"score":score}).encode("utf8")

            self.send_response(200)
            self.send_header("Content-Length",len(fichier))
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            self.wfile.write(fichier)
            return
        self.send_error(404, "URL invalide.")

    def do_GET(self):
        self.params = {}
        if '?' in self.path:
            url = self.path.split('?')
            self.path = url[0]
            for p in url[1].split('&'):
                self.params[p.split('=')[0]] = p.split('=')[1]
        
        if re.match(r"^/soumission/[a-zA-Z0-9_\-#]{1,64}$", self.path):
            hash = self.path.split('/')[-1]

            if hash not in soumissions:
                self.send_error(404, "La soumission n'existe pas")
                return

            fichier = json.dumps(soumissions[hash]).encode("utf8")

            self.send_response(200)
            self.send_header("Content-Length",len(fichier))
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            self.wfile.write(fichier)
            return
        elif self.path == "/soumissions":
            fichier = json.dumps(soumissions_ordonnees).encode("utf8")

            self.send_response(200)
            self.send_header("Content-Length", len(fichier))
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            self.wfile.write(fichier)
            return
        elif self.path == "/scores":
            fichier = json.dumps(scores).encode("utf8")

            self.send_response(200)
            self.send_header("Content-Length", len(fichier))
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            self.wfile.write(fichier)
            return
        elif re.match(r"^/score/[a-zA-Z0-9_\-#]{1,64}$", self.path):
            soumissionaire = base64.b64decode(self.path.split('/')[-1].replace('_','/').replace('-','+').replace('#','=').encode("utf8")).decode("utf8")
            if soumissionaire not in scores:
                self.send_error(404, "Le soumissionaire n'existe pas")
                return

            fichier = json.dumps(scores[soumissionaire]).encode("utf8")

            self.send_response(200)
            self.send_header("Content-Length", len(fichier))
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin",'*')
            self.end_headers()
            self.wfile.write(fichier)
            return
        self.send_error(404, "URL invalide")
        return

def sigterm(signum, frame):
    print("Enregistrement des données")
    with open("./sauvegarde.json", "w") as f:
        f.write(json.dumps({"jeton_admin":jeton_admin,"soumissions":soumissions,"scores":scores}))
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigterm)
    signal.signal(signal.SIGTERM, sigterm)

    print("Chargement des données")
    if os.path.exists("./sauvegarde.json"):
        with open("./sauvegarde.json","r") as f:
            donnees = json.loads(f.read())
            jeton_admin = donnees["jeton_admin"]
            soumissions = donnees["soumissions"]
            scores = donnees["scores"]
    else:
        jeton_admin = base64.b64encode(random.randbytes(32)).decode("utf8").replace('/','_').replace('+','-').replace('=','#')
        print(f"Jeton Admin : {jeton_admin}")
    
    serveurWeb = ThreadingHTTPServer(("0.0.0.0", 5000), defiServeur)

    try:
        serveurWeb.serve_forever()
    except KeyboardInterrupt:
        pass

    serveurWeb.server_close()