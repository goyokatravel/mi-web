-- 18_itinerarios_web.sql · Itinerarios que salen en goyokatravel.com/itinerarios
-- Ejecutar entero en Supabase → SQL Editor. Se puede volver a ejecutar sin problema.

-- 1) Dos columnas nuevas en los itinerarios
--    show_on_web: solo salen en la web los que marques tú (por defecto, ninguno)
--    slug: la dirección de la página, p. ej. "lisboa-3-dias" (la usará también la app en la fase 2)
alter table public.user_itineraries
  add column if not exists show_on_web boolean not null default false,
  add column if not exists slug text;

create unique index if not exists user_itineraries_slug_key
  on public.user_itineraries (slug) where slug is not null;

-- 2) Función que devuelve, en un solo JSON, los itinerarios marcados para la web
--    con sus días, etapas y planes. No devuelve quién lo creó (en la web solo sale la marca).
create or replace function public.web_itineraries()
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(jsonb_agg(it order by it->>'published_at'), '[]'::jsonb)
  from (
    select jsonb_build_object(
      'id', i.id,
      'slug', i.slug,
      'title', i.title,
      'destination', i.destination,
      'country_flag', i.country_flag,
      'description', i.description,
      'total_days', i.total_days,
      'total_places', i.total_places,
      'group_size', i.group_size,
      'budget_per_person', i.budget_per_person,
      'currency', i.currency,
      'photo', coalesce(i.cover_image_url, i.stock_photo_url),
      'photo_credit', i.stock_photo_credit,
      'photo_credit_url', i.stock_photo_credit_url,
      'avg_rating', i.avg_rating,
      'published_at', coalesce(i.published_at, i.created_at),
      'days', (
        select coalesce(jsonb_agg(jsonb_build_object(
                 'day', d.day_number,
                 'title', d.title,
                 'notes', d.notes,
                 'city', l.city,
                 'country', l.country,
                 'plans', (
                   select coalesce(jsonb_agg(jsonb_build_object(
                            'time', p.time_label,
                            'end_time', p.end_time_label,
                            'name', p.place_name,
                            'category', p.category,
                            'note', p.note,
                            'address', p.address,
                            'lat', p.lat,
                            'lng', p.lng,
                            'price', p.price_per_person,
                            'currency', p.currency
                          ) order by p.position), '[]'::jsonb)
                   from public.itinerary_places p
                   where p.day_id = d.id
                 )
               ) order by d.day_number), '[]'::jsonb)
        from public.itinerary_days d
        left join public.trip_legs l on l.id = d.leg_id
        where d.itinerary_id = i.id
      )
    ) as it
    from public.user_itineraries i
    where i.is_public and i.show_on_web
  ) s;
$$;

revoke all on function public.web_itineraries() from public;
grant execute on function public.web_itineraries() to anon, authenticated;

-- 3) Para elegir: lista de itinerarios públicos (copia el resultado y pásaselo a Claude)
select id, title, display_name, total_days, total_places, show_on_web, slug
from public.user_itineraries
where is_public
order by created_at;
