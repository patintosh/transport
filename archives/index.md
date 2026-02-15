
# Archives
  
Cette section regroupe les documents issus de l’ancien site (articles, notes, PDF).
   
## Liste des fichiers

Les documents sont accessibles directement ci-dessous :   
   
{% for file in site.static_files %}
  {% if file.path contains '/archives/' %}
- [{{ file.name }}]({{ file.path }})
  {% endif %}
{% endfor %}

