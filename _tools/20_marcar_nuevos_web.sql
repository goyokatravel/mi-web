-- 20_marcar_nuevos_web.sql · Marca para la web los 9 itinerarios nuevos (pasos 56–64 de la app)
-- y les pone la misma dirección que ya tienen sus páginas en goyokatravel.com/itinerarios.
-- Ejecutar en Supabase → SQL Editor DESPUÉS de 56-60_demo_todos.sql y 61-64_demo_planes.sql.
-- Así, cuando la web se actualice sola desde Supabase, estas páginas no se borran.
update public.user_itineraries u
set show_on_web = true, slug = v.slug
from (values
  ('Granada en un finde', 'granada-finde'),
  ('Málaga en un finde', 'malaga-finde'),
  ('Mallorca en 3 días', 'mallorca-3-dias'),
  ('San Sebastián en un finde', 'san-sebastian-finde'),
  ('Tenerife en 3 días', 'tenerife-3-dias'),
  ('Despedida en Cádiz: playa, pescaíto y fiesta', 'despedida-en-cadiz'),
  ('Mercadillos de Navidad en Alsacia: Estrasburgo y Colmar', 'mercadillos-navidad-alsacia'),
  ('Viaje de fin de carrera: Ibiza en 4 días', 'ibiza-fin-de-carrera-4-dias'),
  ('Escapada rural a Asturias: Picos de Europa y costa', 'asturias-picos-de-europa')
) as v(title, slug)
where u.user_uid = 'c0W07H06H5bYCZfOhZKs6VgeoZL2' and u.title = v.title;

-- Comprobación: deben salir 34 (25 + 9)
select count(*) as en_la_web from public.user_itineraries where show_on_web;
