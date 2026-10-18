-- 19_marcar_demos_web.sql · Marca tus 25 itinerarios demo para la web y les pone su dirección.
-- Fuera quedan las pruebas (PARIS, Madrid prueba) y el de otra usuaria (Tanger).
update public.user_itineraries u
set show_on_web = true, slug = v.slug
from (values
  ('f03bf297-4760-4092-bde5-92f94a1aec62'::uuid, 'roma-5-dias')  -- 5 días en Roma,
  ('71f4ee04-ebef-4ad0-981c-91b9b8363fea'::uuid, 'peru-11-dias')  -- Perú en 11 días,
  ('22bacb93-491a-4413-98c8-9450b2469006'::uuid, 'nueva-york-5-dias')  -- New York in 5 days,
  ('6410563c-0660-4ec3-b335-ee5582c84b48'::uuid, 'sicilia-en-coche-8-dias')  -- Sicilia en coche,
  ('627a02c8-b7a6-41ec-a526-b68f7d5b45ff'::uuid, 'sevilla-3-dias')  -- Sevilla en 3 días,
  ('96c3d0c9-6da7-4bd7-a505-324c055992d2'::uuid, 'vietnam-12-dias')  -- Vietnam de norte a sur,
  ('65ec020d-6285-4b44-8d75-e377c74e5090'::uuid, 'lisboa-3-dias')  -- Lisboa en 3 días,
  ('3307f2a1-cf89-46d2-aa6e-167e1eda946b'::uuid, 'oporto-3-dias')  -- Oporto en 3 días,
  ('44f38da6-3920-4142-aa75-0c18568dc5a3'::uuid, 'amsterdam-3-dias')  -- Ámsterdam en 3 días,
  ('70c52f63-2c11-4ddc-bec3-c74baa919733'::uuid, 'praga-3-dias')  -- Praga en 3 días,
  ('d424709c-53f2-46d4-b0de-1463adcd787a'::uuid, 'budapest-3-dias')  -- Budapest en 3 días,
  ('8f24bfa2-1efd-4ecb-87c1-9ffcd3521d82'::uuid, 'londres-3-dias')  -- Londres en 3 días,
  ('325a4a0c-50c9-4b38-a3bf-2e6621b06696'::uuid, 'paris-3-dias')  -- París en 3 días,
  ('80db93f3-4531-42bb-a601-db803247bba8'::uuid, 'madrid-3-dias')  -- Madrid en 3 días,
  ('1693441d-ec39-4cea-92f3-eeb5749e0308'::uuid, 'uzbekistan-ruta-de-la-seda-9-dias')  -- Uzbekistán,
  ('bb2171d0-da0a-46c9-b399-8a7d845791dd'::uuid, 'valencia-3-dias')  -- Valencia en 3 días,
  ('09abde7b-ea98-4b37-b716-e92272f34a67'::uuid, 'tailandia-12-dias')  -- Tailandia en 12 días,
  ('db885fb1-7378-41d7-a7d9-49eacee7fdac'::uuid, 'mexico-12-dias')  -- México en 12 días,
  ('d937b2f9-88df-4dd0-b67d-5219c56335a8'::uuid, 'japon-11-dias')  -- Japón en 11 días,
  ('ff82d94a-7d11-4635-876d-d3298964149d'::uuid, 'barcelona-3-dias')  -- Barcelona en 3 días,
  ('e1a22915-d946-4e75-a6e4-01b0e56c1b9c'::uuid, 'islandia-en-coche-8-dias')  -- Islandia en coche,
  ('c9292f1e-3028-4554-abfb-db74e4d3fe87'::uuid, 'chile-14-dias')  -- Chile en 14 días,
  ('3671a2ce-35ad-4397-b14c-565e702c5246'::uuid, 'china-3-semanas')  -- China en 3 semanas,
  ('be740893-f9f5-4c3b-b8d7-34ef09733ef2'::uuid, 'brasil-argentina-18-dias')  -- Brasil y Argentina,
  ('37acea5b-0f2c-49e9-94c9-5cf50d3ef2e8'::uuid, 'marruecos-10-dias')  -- Marruecos en 10 días
) as v(id, slug)
where u.id = v.id;

-- Comprobación: deben salir 25
select count(*) as en_la_web from public.user_itineraries where show_on_web;

-- Y esto es lo que leerá la web (expórtalo y pásaselo a Claude)
select web_itineraries();
