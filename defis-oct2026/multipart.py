import atexit
import os
import _io
from typing import BinaryIO, Callable, Iterator


TAILLE_LECTURE_BATCH=256
"""Taille d'une batch de lecture du message"""
TAILLE_MAX_CONTENU_MÉMOIRE=400_000 # 400Ko
"""Taille maximum du contenu d'un élément avant d'être enregistré dans un fichier cache."""
MAX_LONGUEUR_DELIMITEUR=70
"""Longueur maximale d'un délimiteur multipart"""

class TOKEN:
    DÉLIMITEUR="DÉLIMITEUR"
    FIN_LIGNE="FIN_LIGNE"
    EN_TÊTE_NOM="EN_TÊTE_NOM"
    EN_TÊTE_ASSIGNATION="EN_TÊTE_ASSIGNATION"
    EN_TÊTE_LITTÉRAL="EN_TÊTE_LITTÉRAL"
    EN_TÊTE_DELIMITEUR="EN_TÊTE_DELIMITEUR"
    EN_TÊTE_PARAM="EN_TÊTE_PARAM"
    EN_TÊTE_PARAM_ASSIGNATION="EN_TÊTE_PARAM_ASSIGNATION"
    CONTENU="CONTENU"
    CONTENU_CACHE="CONTENU_CACHE"
    FIN_MESSAGE="FIN_MESSAGE"

class EnTête:
    def __init__ (self, nom : str, valeur : str, params : dict[str,str]):
        self.nom : str = nom
        self.valeur : str = valeur
        self.params : dict[str,str] = params
    
    def __getitem__ (self,k : str) -> str:
        return self.params[k.lower()]
    def get(self, k : str) -> str:
        if k.lower() in self.params:
            return self.params[k.lower()]
        return None
    def __setitem__ (self,k : str,v : str):
        self.params[k.lower()]=v
    def __missing__ (self,k : str) -> bool:
        return k.lower() not in self.params
    def __contains__ (self,k : str) -> bool:
        return k.lower() in self.params
    def __iter__ (self):
        return self.params.__iter__()

class Partie:
    def __init__(self, en_tetes, donnees_fonc):
        self.en_tetes : dict[str,EnTête] = en_tetes
        self._lire_donnees : Callable[[int|None, str|None], bytes|str] = donnees_fonc
        self._donnees_curseur : int = 0
    
    def lire(self, octets : int | None = None, décoder : str | None=None) -> bytes | str:
        """Renvoie `octets` d'octets du contenu de la partie. Si `octets == None`, 
        renvera l'entièreté du message. Si `décoder != None`, tentera de décoder 
        le message selon l'encodage spécifé (ex.: `utf8` tentera de décoder le 
        message en `utf8`), sinon retournera le message en octets.

        Args:
            octets (int | None, optional): Nombre d'octets à lire. Si `None`, renvoie la totalité du contenu. Défaut : None.
            décoder (str | None, optional): Encodage pour décoder le message. Si `None` ou si le décodage échoue, renvoie sous forme d'octets. Défaut : None.
        Returns:
            (bytes | str): Les données de cette partie du message.
        """
        if décoder:
            try:
                return self._lire_donnees(self, octets).decode(décoder)
            except Exception as e:
                print(e)
                return self._lire_donnees(self, octets)
        else:
            return self._lire_donnees(self, octets)

    def __getitem__ (self, k : str) -> EnTête:
        return self.en_tetes[k.lower()]
    def get(self, k : str) -> EnTête:
        if k.lower() in self.en_tetes:
            return self.en_tetes[k.lower()]
        return None
    def __missing__ (self, k : str) -> bool:
        return k.lower() not in self.en_tetes
    def __contains__ (self,k : str) -> bool:
        return k.lower() in self.en_tetes
    def __iter__(self):
        return self.en_tetes.__iter__()

class Multipart:
    _instances = 0

    def __init__(self, rfile : BinaryIO, message_taille : int) -> dict:
        self._instance = Multipart._instances
        Multipart._instances += 1
        atexit.register(self.détruire)
        self.cache : list[BinaryIO] = []
        tokens = self.segmenter(rfile, message_taille)
        self.parties : list[Partie] = self.parser(tokens)
        pass

    def segmenter(self, rfile : BinaryIO, message_taille : int) -> list[dict]:
        class ÉTAT:
            LIT_DÉLIMITEUR=0
            LIT_EN_TÊTE=1
            LIT_EN_TÊTE_PARAMS=2
            LIT_EN_TÊTE_STRING=3
            LIT_CONTENU=4
            LIT_CONTENU_EN_CACHE=5
            TERMINÉ=6

        état=ÉTAT.LIT_DÉLIMITEUR

        mot = b""
        delimiteur = None
        tokens = []
        contenu = b""
        octets_lus = 0

        while état != ÉTAT.TERMINÉ:
            if octets_lus >= message_taille:
                raise Exception("[ERREUR] Le message n'est pas complet")

            lecture = min(TAILLE_LECTURE_BATCH, message_taille-octets_lus)
            if état != ÉTAT.LIT_CONTENU_EN_CACHE:
                for c in rfile.read(lecture):
                    c = c.to_bytes(1)
                    octets_lus += 1
                    match état:
                        case ÉTAT.LIT_DÉLIMITEUR:
                            if 0 < len(mot) <= 2 and mot != b'-'*len(mot):
                                raise Exception(f"[ERREUR] '--' attendu, obtenu {mot}")
                                return None
                            if len(mot) > 2 and c == b'\n':
                                delimiteur = mot[:-1] if mot[-1] == ord(b'\r') else mot
                                tokens.append({
                                        "type":TOKEN.DÉLIMITEUR,
                                        "valeur":delimiteur.decode("utf8")
                                    })
                                tokens.append({
                                        "type":TOKEN.FIN_LIGNE,
                                        "valeur":"\r\n" if mot[-1] == ord(b'\r') else "\n"
                                    })
                                mot = b""
                                état=ÉTAT.LIT_EN_TÊTE
                                continue
                            mot += c
                            continue
                        case ÉTAT.LIT_EN_TÊTE:

                            if c == b' ':
                                continue
                            if c == b'"':
                                if len(mot) != 0:
                                    print("[ERREUR] obtenu '\"', attendu : ':', ';', ' ' ou <caractère>")
                                    print(mot+c)
                                    print('~'*len(mot)+'^')
                                    raise Exception()
                                tokens.append({
                                        "type":TOKEN.EN_TÊTE_GUILLEMET,
                                        "valeur":'"'
                                    })
                                état=ÉTAT.LIT_EN_TÊTE_STRING
                                continue
                            if c == b':':
                                tokens.append({
                                        "type":TOKEN.EN_TÊTE_NOM,
                                        "valeur":mot.decode("utf8").lower()
                                    })
                                tokens.append({
                                    "type":TOKEN.EN_TÊTE_ASSIGNATION,
                                    "valeur":":"
                                })
                                mot = b""
                                continue
                            if c == b';':
                                tokens.append({
                                        "type":TOKEN.EN_TÊTE_LITTÉRAL,
                                        "valeur":mot.decode("utf8")
                                    })
                                tokens.append({
                                        "type":TOKEN.EN_TÊTE_DELIMITEUR,
                                        "valeur":';'
                                    })
                                mot = b""
                                état=ÉTAT.LIT_EN_TÊTE_PARAMS
                                continue
                            if c == b'\n':
                                if len(mot) > 1 or (len(mot) > 0 and mot[-1] != ord(b'\r')):
                                    tokens.append({
                                            "type": TOKEN.EN_TÊTE_LITTÉRAL,
                                            "valeur": (mot[:-1] if mot[-1] == ord(b'\r') else mot).decode("utf8")
                                        })

                                tokens.append({
                                        "type":TOKEN.FIN_LIGNE,
                                        "valeur":"\r\n" if len(mot) >= 1 and mot[-1] == ord(b'\r') else '\n'
                                    })
                                mot = b""
                                if len(tokens) > 1 and tokens[-2]["type"] == TOKEN.FIN_LIGNE:
                                    état = ÉTAT.LIT_CONTENU
                                continue
                            mot += c
                        case ÉTAT.LIT_EN_TÊTE_PARAMS:
                            if c == b' ':
                                continue
                            if c == b'=':
                                tokens.append({
                                        "type":TOKEN.EN_TÊTE_PARAM,
                                        "valeur":mot.decode("utf8").lower()
                                    })
                                tokens.append({
                                        "type":TOKEN.EN_TÊTE_PARAM_ASSIGNATION,
                                        "valeur":'='
                                    })
                                mot=b""
                                continue
                            if c == b'"':
                                if len(mot) != 0:
                                    print("[ERREUR] obtenu '\"', attendu : '=', ';', ' ' ou <caractère>")
                                    print(mot+c)
                                    print(b'~'*len(mot)+b'^')
                                    raise Exception()
                                état = ÉTAT.LIT_EN_TÊTE_STRING
                                continue
                            if c == b';':
                                # Le littéral précédent pourrait avoir été un string entre guillemets
                                if len(mot) != 0:
                                    tokens.append({
                                            "type":TOKEN.EN_TÊTE_LITTÉRAL,
                                            "valeur":mot.decode("utf8")
                                        })
                                tokens.append({
                                        "type":TOKEN.EN_TÊTE_DELIMITEUR,
                                        "valeur":';'
                                    })
                                mot = b""
                                continue
                            if c == b'\n':
                                tokens.append({
                                        "type":TOKEN.FIN_LIGNE,
                                        "valeur":"\r\n" if len(mot) >= 1 and mot[-1] == ord(b'\r') else '\n'
                                    })
                                if len(mot) >= 1 and mot[-1] == ord(b'\r'):
                                    mot = mot[:-1]

                                # Le littéral précédent pourrait avoir été un string entre guillemets
                                if len(mot) != 0:
                                    tokens.append({
                                        "type": TOKEN.EN_TÊTE_LITTÉRAL,
                                        "valeur": mot.decode("utf8")
                                    })
                                état = ÉTAT.LIT_EN_TÊTE
                                continue
                            mot += c
                        case ÉTAT.LIT_EN_TÊTE_STRING:
                            if c == b'"':
                                tokens.append({
                                        "type":TOKEN.EN_TÊTE_LITTÉRAL,
                                        "valeur":mot.decode("utf8")
                                    })
                                mot = b""
                                état = ÉTAT.LIT_EN_TÊTE_PARAMS
                                continue
                            mot += c
                        case ÉTAT.LIT_CONTENU:
                            if len(contenu)+1 > TAILLE_MAX_CONTENU_MÉMOIRE:
                                if not os.path.exists("./cache"):
                                    os.mkdir("./cache")
                                if not os.path.exists(f"./cache/{self._instance}"):
                                    os.mkdir(f"./cache/{self._instance}")

                                f = open(f"./cache/{self._instance}/{len(self.cache)}","wb+")  # noqa: SIM115
                                self.cache.append(f)
                                f.write(contenu+c)
                                contenu = contenu[-(len(b"\r\n")+MAX_LONGUEUR_DELIMITEUR+len(b"-")):]+c
                                état = ÉTAT.LIT_CONTENU_EN_CACHE
                                break

                            # \r?\n<délimiteur>[\r?\n|--]
                            if (contenu[-(len(b"\n")+len(delimiteur)+len(b"-")):]+c)[:-2] == b"\n"+delimiteur:
                                est_CRLF = contenu[-(len(b"\r\n")+len(delimiteur)+len(b"-"))] == ord(b'\r')
                                est_fin = contenu[-1] == ord(b'-') and c == b'-'
                                longueur_contenu = len(contenu) - (2 if est_CRLF else 1) - len(delimiteur) - 1
                                tokens.append({
                                    "type":TOKEN.CONTENU,
                                    "valeur":contenu[:longueur_contenu]
                                })
                                tokens.append({
                                        "type": TOKEN.FIN_LIGNE,
                                        "valeur": "\r\n" if est_CRLF else '\n'
                                    })
                                tokens.append({
                                        "type": TOKEN.DÉLIMITEUR,
                                        "valeur": delimiteur.decode("utf8")
                                    })
                                if not est_fin:
                                    if contenu[-1] != ord('\n') and contenu[-1] != ord(b'\r') and c != b'\n':
                                        print("[ERREUR] '\r\n' ou '\n' attendu")
                                        print(b"..."+contenu[:longueur_contenu]+c)
                                        print(b'~'*(longueur_contenu-1)+b'^')
                                        raise Exception()
                                    tokens.append({
                                            "type": TOKEN.FIN_LIGNE,
                                            "valeur": "\r\n" if contenu[-1] == ord(b'\r') else '\n'
                                        })
                                    état = ÉTAT.LIT_EN_TÊTE
                                    contenu = b""
                                    continue
                                if est_fin:
                                    tokens.append({
                                            "type": TOKEN.FIN_MESSAGE,
                                            "valeur": "--"
                                        })
                                    état = ÉTAT.TERMINÉ
                                    contenu = b""
                                    break
                            contenu += c
            else:
                contenu += rfile.read(lecture)
                octets_lus += lecture
                l_delimiteur = len(b"\r\n")+len(delimiteur)+len(b"--")
                for i in range(l_delimiteur, len(contenu)):
                    # \r?\n<délimiteur>[\r?\n|--]
                    if ( contenu[i-(l_delimiteur-1) : i] )[:-2] == b"\n"+delimiteur:
                        est_CRLF = contenu[i-l_delimiteur] == b'\r'
                        est_fin = contenu[i-2:i] == b"--"
                        longueur_contenu = i-1 - (2 if est_CRLF else 1) - len(delimiteur) - 2
                        self.cache[-1].write(contenu[len("\r\n")+MAX_LONGUEUR_DELIMITEUR+len("--"):longueur_contenu])
                        self.cache[-1].seek(0)
                        rfile.seek(i-len(contenu),os.SEEK_CUR)
                        tokens.append({
                                "type":TOKEN.CONTENU_CACHE,
                                "valeur":len(self.cache)-1
                            })
                        tokens.append({
                                "type": TOKEN.FIN_LIGNE,
                                "valeur": "\r\n" if est_CRLF else '\n'
                            })
                        tokens.append({
                                "type": TOKEN.DÉLIMITEUR,
                                "valeur": delimiteur.decode("utf8")
                            })
                        if not est_fin:
                            if contenu[i-1:i+1] != "\r\n" and contenu[i] != '\n':
                                print("[ERREUR] '\r\n' ou '\n' attendu")
                                print(b"..."+contenu[i-longueur_contenu:i+1])
                                print(b'~'*(longueur_contenu-1)+b'^')
                                raise Exception()
                            tokens.append({
                                    "type": TOKEN.FIN_LIGNE,
                                    "valeur": "\r\n" if contenu[i-1] == ord(b'\r') else '\n'
                                })
                            état = ÉTAT.LIT_EN_TÊTE
                            contenu=b""
                            continue
                        if est_fin:
                            tokens.append({
                                    "type": TOKEN.FIN_MESSAGE,
                                    "valeur": "--"
                                })
                            état = ÉTAT.TERMINÉ
                            contenu=b""
                            break
                if état != ÉTAT.TERMINÉ:
                    if octets_lus >= message_taille:
                        raise Exception("[ERREUR]Le message n'est pas complet")
                    
                    tampon = len("\r\n")+MAX_LONGUEUR_DELIMITEUR+len("--")
                    self.cache[-1].write(contenu[tampon:])
                    contenu = contenu[-tampon:]
        return tokens
    
    def parser(self,tokens : list[dict]) -> list[Partie]:
        class ÉTAT:
            LIT_EN_TÊTE=0
            LIT_EN_TÊTE_PARAMS=1
            LIT_CONTENU=2
        
        état = ÉTAT.LIT_EN_TÊTE

        parties : list[Partie] = []
        en_tetes : dict[str,EnTête] = {}
        en_tete_actuel : EnTête
        phrase : list[dict] = []

        for t in tokens:
            match état:
                case ÉTAT.LIT_EN_TÊTE:
                    match t["type"]:
                        case TOKEN.EN_TÊTE_DELIMITEUR | TOKEN.FIN_LIGNE:
                            if len(phrase) > 3 or ( len(phrase) == 3 and (
                                    phrase[0]["type"] != TOKEN.EN_TÊTE_NOM or
                                    phrase[1]["type"] != TOKEN.EN_TÊTE_ASSIGNATION or
                                    phrase[2]["type"] != TOKEN.EN_TÊTE_LITTÉRAL
                                )):
                                print("[ERREUR] <EN_TÊTE_NOM>,<EN_TÊTE_ASSIGNATION>,<EN_TÊTE_LITTÉRAL>,<EN_TÊTE_DÉLIMITEUR|FIN_LIGNE>|<DÉLIMITEUR>,<FIN_LIGNE>|<FIN_LIGNE> attendu.")
                                phrase_str=""
                                for t in phrase:
                                    phrase_str += f"<{t["type"]}>,"
                                print(phrase_str)
                                print('~'*len(phrase_str))
                                raise Exception()
                            if len(phrase) == 0:
                                phrase = []
                                état = ÉTAT.LIT_CONTENU
                                continue
                            if len(phrase) == 1 and phrase[0]["type"] == TOKEN.DÉLIMITEUR:
                                phrase = []
                                continue
                            en_tete_actuel = EnTête(
                                nom=phrase[0]["valeur"],
                                valeur=phrase[2]["valeur"],
                                params={}
                            )
                            en_tetes[phrase[0]["valeur"]]=en_tete_actuel
                            phrase = []
                            if t["type"] == TOKEN.EN_TÊTE_DELIMITEUR:
                                état = ÉTAT.LIT_EN_TÊTE_PARAMS
                            continue
                    phrase.append(t)
                case ÉTAT.LIT_EN_TÊTE_PARAMS:
                    match t["type"]:
                        case TOKEN.EN_TÊTE_DELIMITEUR | TOKEN.FIN_LIGNE:
                            if len(phrase) != 3 or ( len(phrase) != 3 and (
                                    phrase[0]["type"] != TOKEN.EN_TÊTE_PARAM or
                                    phrase[1]["type"] != TOKEN.EN_TÊTE_PARAM_ASSIGNATION or
                                    phrase[2]["type"] != TOKEN.EN_TÊTE_LITTÉRAL
                                )):
                                print("[ERREUR] <EN_TÊTE_PARAM>,<EN_TÊTE_PARAM_ASSIGNATION>,<EN_TÊTE_LITTÉRAL> attendu.")
                                phrase_str=""
                                for t in phrase:
                                    phrase_str += f"<{t["type"]}>,"
                                print(phrase_str)
                                print('~'*len(phrase_str))
                                raise Exception()
                            en_tete_actuel[phrase[0]["valeur"]] = phrase[2]["valeur"]
                            phrase = []
                            if t["type"] == TOKEN.FIN_LIGNE:
                                état = ÉTAT.LIT_EN_TÊTE
                            continue
                    phrase.append(t)
                case ÉTAT.LIT_CONTENU:
                    if (t["type"] == TOKEN.FIN_LIGNE or t["type"] == TOKEN.FIN_MESSAGE) and len(phrase) == 3 and (
                            (phrase[0]["type"] == TOKEN.CONTENU or phrase[0]["type"] == TOKEN.CONTENU_CACHE) and 
                            phrase[1]["type"] == TOKEN.FIN_LIGNE and
                            phrase[2]["type"] == TOKEN.DÉLIMITEUR
                        ):

                        partie : Partie
                        if phrase[0]["type"] == TOKEN.CONTENU:
                            def lire(self1, octets : int | None = None, phrase=phrase) -> bytes|str:
                                if not octets:
                                    return phrase[0]["valeur"]
                                ret = phrase[0]["valeur"][self1._donnees_curseur : self1._donnees_curseur+octets]
                                self1._donnees_curseur += octets
                                return ret
                            partie = Partie(en_tetes=en_tetes, donnees_fonc=lire)
                        else:
                            def lire(self1, octets : int | None = None, phrase=phrase) -> bytes|str:
                                if not octets:
                                    return self.cache[phrase[0]["valeur"]].read()
                                return self.cache[phrase[0]["valeur"]].read(octets)
                            partie = Partie(en_tetes=en_tetes, donnees_fonc=lire)

                        parties.append(partie)
                        en_tetes = {}
                        phrase = []
                        if t["type"] == TOKEN.FIN_LIGNE:
                            état = ÉTAT.LIT_EN_TÊTE
                        else:
                            état = None
                        continue
                    elif len(phrase) > 4:
                        print("[ERREUR] <CONTENU|CONTENU_CACHE>,<FIN_LIGNE>,<DÉLIMITEUR>,<FIN_LIGNE> attendu.")
                        phrase_str=""
                        for t in phrase:
                            phrase_str += f"<{t["type"]}>,"
                        print(phrase_str)
                        print('~'*len(phrase_str))
                        raise Exception()

                    phrase.append(t)
        return parties

    def __enter__(self):
        return self
    def __exit__(self):
        self.détruire()

    def détruire(self):
        for i in range(len(self.cache)):
            self.cache[i].close()
            os.remove(f"./cache/{self._instance}/{i}")
            if len(os.listdir(f"./cache/{self._instance}")) == 0:
                os.rmdir(f"./cache/{self._instance}")
            if len(os.listdir("./cache")) == 0:
                os.rmdir("./cache")

class MultipartFormdata(Multipart):
    def __init__(self, rfile : BinaryIO, message_taille : int):
        super().__init__(rfile, message_taille)

        self._parties_nommées :dict = {}
        for p in self.parties:
            if "Content-Disposition" not in p or "name" not in p["Content-Disposition"]:
                raise Exception("Le message n'est pas un 'multipart/form-data'")
            self._parties_nommées[p["Content-Disposition"]["name"]]=p

    def __getitem__(self, k : str) -> Partie:
        return self._parties_nommées[k.lower()]
    def get(self, k : str) -> str:
        if k.lower() in self._parties_nommées:
            return self._parties_nommées[k.lower()]
        return None
    def __missing__(self, k : str) -> bool:
        return k.lower() not in self._parties_nommées
    def __contains__(self,k : str) -> bool:
        return k.lower() in self._parties_nommées
    def __iter__ (self) -> Iterator[[str,Partie]]:
        return self._parties_nommées.__iter__()