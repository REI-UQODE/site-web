<!DOCTYPE html>

<?php
define("jsonMailingList", "mailingUQODE.json");
define("fichierNouvellesInscriptions", ".nouvelles_inscriptions");

if ($_SERVER["REQUEST_METHOD"] == "POST")
{
	$prenom = htmlspecialchars($_POST['prenom']);
	$nomFamille = htmlspecialchars($_POST['nomFamille']);
	$programme = htmlspecialchars($_POST['programme']);
	$courriel = htmlspecialchars($_POST['courriel']);
	
	if ($prenom == null || $nomFamille == null || $programme == null || $courriel == null)
	{http_response_code(400); exit();}
	
	if (!filter_var($courriel, FILTER_VALIDATE_EMAIL))
	{$erreur = "Veuillez réessayer avec une adresse courriel valide.";}
	
	else //pas d'erreur facile à détecter
	{
		/* Envoi d'un courriel de confirmation:
		 * Malheureusement, hoster notre propre serveur de courriel serait vraiment compliqué, voire impossible sans l'accord du STI,
		 *   et utiliser notre adresse @uqo.ca ou un gmail serait au moins aussi compliqué et nécessiterait un monitorage constant.
		 * Je commente donc cette section (qui n'est d'ailleurs vraiment pas complète) pour l'instant...
		 * Si on décommente ça un jour, $erreur est une variable dont la définition indique un erreur. Son contenu (string) doit être affiché à l'écran (inséré dans le html).
		 * 
		 * $to = "recipient@example.com";
		 * $subject = "Test Email from PHP";
		 * $body = "Hello,\n\nThis is a test message sent via PHP's mail function.";
		 * $headers = "From: webmaster@yourdomain.com\r\nReply-To: webmaster@yourdomain.com\r\nX-Mailer: PHP/{phpversion()}";
		 * 
		 * if (mail($to, $subject, $body, $headers))
		 * {error_log("Email successfully sent!");}
		 * else
		 * {$erreur = "Impossible d'envoyer un courriel à cette adresse.";}
		 */
		
		try
		{
			$inscrits = json_decode(file_get_contents(jsonMailingList), true);
			
			foreach ($inscrits as $inscrit)
			{
				if ($inscrit['courriel'] == $courriel)
				{$erreur = "Cette adresse courriel est déjà inscrite aux courriels de l'UQODE."; break;}
				else if ($inscrit['prenom'] == $prenom && $inscrit['nomFamille'] == $nomFamille)
				{$erreur = "Vous êtes déjà inscrit aux courriels de l'UQODE."; break;}
			}
		}
		catch (Exception $e)
		{
			error_log("ERREUR: Impossible d'ouvrir ou de parser le fichier JSON {jsonMailingList}!");
			$erreur = "Un problème technique nous empêche de procéder à l'inscription. Réessayez plus tard.";
		}
		
		if (!isset($erreur)) //vraiment pas d'erreur
		{
			error_log("Inscription de $prenom $nomFamille ($courriel) au mailing.");
			
			$inscrits[] = ["prenom" => $prenom, "nomFamille" => $nomFamille, "programme" => $programme, "courriel" => $courriel];
			file_put_contents(jsonMailingList, json_encode($inscrits, JSON_PRETTY_PRINT));
			
			try
			{
				$nbreNouvellesInscriptions = file_get_contents(fichierNouvellesInscriptions);
				$nbreNouvellesInscriptions = (string) ((int) $nbreNouvellesInscriptions + 1);
				error_log("Il s'agit de la {$nbreNouvellesInscriptions}e nouvelle inscription.");
				file_put_contents(fichierNouvellesInscriptions, $nbreNouvellesInscriptions);
			}
			catch (Exception $e)
			{
				error_log("Il s'agit de la 1ère nouvelle inscription.");
				file_put_contents(fichierNouvellesInscripions, "1");
			}
		}
	}
}
else
{http_response_code(400); exit();}
?>

<html>
<head>
	<title>Inscription aux nouvelles de l'UQODE</title>
	<meta charset="UTF-8">
	
	<style>
		body
		{
			background-color: #870B86;
			margin: 0;
			font-family: Helvetica, sans-serif, Arial;
		}
		
		#page
		{
			background-color: #EBEBEB;
			padding: 30px;
			margin: 0 150px;
		}
		
		a.bouton
		{
			background-color: #9D079C;
			margin: 0.5em;
			padding: 0.5em 1em;
			border-radius: 0.5em;
			display: inline-block;
			border: 0;
			color: white;
			text-decoration: none;
			font-size: 1.1em;
			box-shadow: 0 0.5em 1em #0003;
			transition: 300ms;
			cursor: pointer;
		}
	</style>
</head>

<body>
	<div id="page">
		<?php
		if (isset($erreur))
		{
			echo "<h1>$erreur</h1>";
			echo "<a class='bouton' href='mailing.html'>Revenir au formulaire d'inscription</a>";
		}
		else
		{
			echo "<h1>Tu as été abonné avec succès.</h1>";
			echo "<a class='bouton' href='https://rei-uqode.ca'>Revenir au site web</a>";
		}
		?>
		<p>N'oublie pas de rejoindre notre <a href="https://discord.gg/XNPFzumVzb">serveur discord</a> pour ne rien manquer des activités du REI et de l'UQODE!</p>
	</div>
</body>
</html>
