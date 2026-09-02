function montrerUsager (nom, service)
		{
			
			if (service == "Matrix")
			{
				switch (nom)
				{
					case 'Nicolas':
						hoverbox = document.getElementById('hoverbox-Nicolas');
						hoverbox.innerHTML = "@nicolas:rei-uqode.ca";
						break;
					
					case 'Godbout':
						hoverbox = document.getElementById('hoverbox-Godbout');
						hoverbox.innerHTML = "@gyoo18:gyoo.ca";
						break;
				}
			}
			
			else if (service == "Discord")
			{
				switch (nom)
				{
					case 'Nicolas':
						hoverbox = document.getElementById('hoverbox-Nicolas');
						hoverbox.innerHTML = "@nicolas.6464 (@Nico64)";
						break;
					
					case 'Godbout':
						hoverbox = document.getElementById('hoverbox-Godbout');
						hoverbox.innerHTML = "@gyoostudio";
						break;
					
					case 'Lafleur':
						hoverbox = document.getElementById('hoverbox-Lafleur');
						hoverbox.innerHTML = "@mustangguy44 (@Stang_Boy)";
						break;
					
					case 'Richard':
						hoverbox = document.getElementById('hoverbox-Richard');
						hoverbox.innerHTML = "@minato061215 (@Richard)";
						break;
					
					case 'Sebastien':
						hoverbox = document.getElementById('hoverbox-Sebastien');
						hoverbox.innerHTML = "@grosr (@R)";
						break;
					
					case 'Madiha':
						hoverbox = document.getElementById('hoverbox-Madiha');
						hoverbox.innerHTML = "@madiha_20074_06021 (@Madiha)";
						break;
					
					case 'Hugo':
						hoverbox = document.getElementById('hoverbox-Hugo');
						hoverbox.innerHTML = "@hugus0916 (@Hugo t)";
						break;
					
					case 'Lindor':
						hoverbox = document.getElementById('hoverbox-Lindor');
						hoverbox.innerHTML = "@lindordiop_42234 (@LindorDiop)";
				}
			}
			
			hoverbox.style.display = "inline-block";
		}
		
		function cacherUsager (nom)
		{document.getElementById('hoverbox-' + nom).style.display = "none";}
