---
layout: jp_page
title: "FAQ"
description: ""
group: navigation
---
{% include JB/setup %}
<ul>
{% for post in site.categories.jp %}
<li><a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
{% endfor %}
</ul>
