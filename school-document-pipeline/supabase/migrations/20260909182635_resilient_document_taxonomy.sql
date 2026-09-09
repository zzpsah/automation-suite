begin;

create table public.document_categories (
  category_key text primary key check (category_key ~ '^[a-z0-9_]+$'),
  created_at timestamptz not null default now()
);

alter table public.document_categories enable row level security;

create policy "reviewers read stable category keys"
on public.document_categories for select
to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

insert into public.document_categories (category_key)
values
  ('bseb'),('examination'),('registration'),('student'),('admission'),
  ('payment_fee'),('scholarship'),('udise'),('school_administration'),
  ('teacher_staff'),('attendance'),('infrastructure'),('building_repair'),
  ('inspection'),('meeting'),('training'),('government_order'),
  ('district_office'),('block_office'),('notice_circular'),('academic'),
  ('computer_science'),('data_submission'),('portal_technical'),
  ('deadline_urgent'),('finance_accounts'),('procurement'),
  ('general_information'),('other');

create table public.document_category_definitions (
  id bigint generated always as identity primary key,
  category_key text not null references public.document_categories(category_key),
  version integer not null check (version > 0),
  display_name text not null,
  description text,
  aliases text[] not null default '{}'::text[],
  office_terms text[] not null default '{}'::text[],
  content_terms text[] not null default '{}'::text[],
  active boolean not null default true,
  sort_order integer not null default 100,
  valid_from timestamptz not null default now(),
  valid_to timestamptz,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (category_key, version),
  check (valid_to is null or valid_to > valid_from)
);

create unique index document_category_one_current_version_idx
  on public.document_category_definitions (category_key)
  where valid_to is null;

create index document_category_active_sort_idx
  on public.document_category_definitions (active, sort_order)
  where valid_to is null;

alter table public.document_category_definitions enable row level security;

create policy "public reads active category definitions"
on public.document_category_definitions for select
to anon
using (active and valid_to is null);

create policy "reviewers read category history"
on public.document_category_definitions for select
to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers insert category versions"
on public.document_category_definitions for insert
to authenticated
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create policy "reviewers close category versions"
on public.document_category_definitions for update
to authenticated
using (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'))
with check (((select auth.jwt()) -> 'app_metadata' ->> 'role') in ('reviewer','admin'));

create function public.preserve_category_definition_history()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if new.category_key is distinct from old.category_key
    or new.version is distinct from old.version
    or new.display_name is distinct from old.display_name
    or new.description is distinct from old.description
    or new.aliases is distinct from old.aliases
    or new.office_terms is distinct from old.office_terms
    or new.content_terms is distinct from old.content_terms
    or new.sort_order is distinct from old.sort_order
    or new.valid_from is distinct from old.valid_from
    or new.created_by is distinct from old.created_by
    or new.created_at is distinct from old.created_at then
    raise exception 'Category definitions are immutable. Close this version and insert a new version.';
  end if;
  return new;
end;
$$;

revoke all on function public.preserve_category_definition_history() from public, anon, authenticated;

create trigger preserve_category_definition_history_trigger
before update on public.document_category_definitions
for each row execute function public.preserve_category_definition_history();

insert into public.document_category_definitions
  (category_key, version, display_name, description, aliases, office_terms, content_terms, sort_order)
values
  ('bseb',1,'BSEB','Bihar School Examination Board work',array['Bihar Board','बिहार बोर्ड'],array['BSEB','बिहार विद्यालय परीक्षा समिति'],array['registration card','admit card','dummy card','पंजीयन','परीक्षा समिति'],10),
  ('examination',1,'Examination','Examination forms and operations',array['Exam','परीक्षा'],array[]::text[],array['exam','examination','परीक्षा','admit card'],20),
  ('registration',1,'Registration','Student or institutional registration',array['पंजीकरण','पंजीयन'],array[]::text[],array['registration','पंजीकरण','पंजीयन'],30),
  ('student',1,'Student','Student records and instructions',array['विद्यार्थी','छात्र'],array[]::text[],array['student','विद्यार्थी','छात्र'],40),
  ('admission',1,'Admission','Admission and enrolment work',array['नामांकन','enrolment'],array['OFSS'],array['admission','नामांकन','CAF','selection list'],50),
  ('payment_fee',1,'Payment / Fee','Fees, payments and financial deadlines',array['Fee','Payment','शुल्क','भुगतान'],array[]::text[],array['fee','payment','शुल्क','भुगतान','challan'],60),
  ('scholarship',1,'Scholarship','Scholarship and student-benefit work',array['छात्रवृत्ति'],array['e-Kalyan','National Scholarship Portal'],array['scholarship','छात्रवृत्ति','प्रोत्साहन'],70),
  ('udise',1,'UDISE','UDISE school-data work',array['UDISE+'],array['UDISE','UDISE+'],array['UDISE','school profile'],80),
  ('school_administration',1,'School Administration','School office and administrative work',array['School Office','विद्यालय प्रशासन'],array['विद्यालय कार्यालय','School Office'],array['administration','विद्यालय प्रशासन'],90),
  ('teacher_staff',1,'Teacher / Staff','Teacher and staff instructions',array['Staff','Teacher','शिक्षक','कर्मी'],array[]::text[],array['teacher','staff','शिक्षक','कर्मी'],100),
  ('attendance',1,'Attendance','Student or staff attendance',array['उपस्थिति'],array[]::text[],array['attendance','उपस्थिति'],110),
  ('infrastructure',1,'Infrastructure','School infrastructure reporting',array['अवसंरचना'],array[]::text[],array['infrastructure','अवसंरचना','facility'],120),
  ('building_repair',1,'Building / Repair','Building, maintenance and repair work',array['Repair','भवन','मरम्मत'],array[]::text[],array['building','repair','भवन','मरम्मत'],130),
  ('inspection',1,'Inspection','Official inspection and compliance',array['निरीक्षण'],array[]::text[],array['inspection','निरीक्षण'],140),
  ('meeting',1,'Meeting','Official meetings and attendance',array['बैठक'],array[]::text[],array['meeting','बैठक'],150),
  ('training',1,'Training','Teacher or staff training',array['प्रशिक्षण'],array[]::text[],array['training','प्रशिक्षण'],160),
  ('government_order',1,'Government Order','Orders issued by government authorities',array['Govt Order','सरकारी आदेश'],array['Government of Bihar','बिहार सरकार','जिला पदाधिकारी'],array['order','आदेश','संकल्प'],170),
  ('district_office',1,'District Office','District and DEO instructions',array['DEO','District','जिला कार्यालय'],array['District Education Officer','जिला शिक्षा पदाधिकारी','DEO','District Magistrate','जिला पदाधिकारी'],array['district','जिला'],180),
  ('block_office',1,'Block Office','Block and BEO instructions',array['BEO','प्रखंड कार्यालय'],array['Block Education Officer','प्रखंड शिक्षा पदाधिकारी','BEO'],array['block office','प्रखंड'],190),
  ('notice_circular',1,'Notice / Circular','Official notices, letters and circulars',array['Notice','Circular','पत्र','सूचना','परिपत्र'],array[]::text[],array['notice','circular','पत्रांक','ज्ञापांक','सूचना','परिपत्र'],200),
  ('academic',1,'Academic','Teaching, curriculum and academic work',array['शैक्षणिक'],array[]::text[],array['academic','curriculum','शैक्षणिक','पाठ्यक्रम'],210),
  ('computer_science',1,'Computer Science','Computer science and ICT learning',array['ICT','Computer','कंप्यूटर'],array[]::text[],array['computer science','ICT','कंप्यूटर'],220),
  ('data_submission',1,'Data Submission','Required data entry, upload or reporting',array['Reporting','डेटा जमा'],array[]::text[],array['submit data','upload data','report','प्रतिवेदन','डेटा'],230),
  ('portal_technical',1,'Portal / Technical Issue','Portal access and technical problems',array['Portal','Technical','तकनीकी समस्या'],array[]::text[],array['portal','login','server','technical','तकनीकी','लॉगिन'],240),
  ('deadline_urgent',1,'Deadline / Urgent Action','Time-sensitive compliance and deadlines',array['Urgent','Deadline','अत्यावश्यक','अंतिम तिथि'],array[]::text[],array['deadline','last date','urgent','अंतिम तिथि','तत्काल','अविलंब'],250),
  ('finance_accounts',1,'Finance / Accounts','Accounts, funds and financial records',array['Accounts','Finance','लेखा','कोष'],array['Treasury','कोषागार'],array['account','fund','finance','लेखा','कोष'],260),
  ('procurement',1,'Procurement','Purchasing and tender work',array['Purchase','Tender','क्रय','निविदा'],array[]::text[],array['procurement','purchase','tender','क्रय','निविदा'],270),
  ('general_information',1,'General Information','Useful information with no better category',array['Information','जानकारी'],array[]::text[],array['information','जानकारी'],900),
  ('other',1,'Other','Unclassified material requiring review',array['Unclassified','अन्य'],array[]::text[],array[]::text[],999);

alter table public.documents add column category_key text;
alter table public.documents add column category_source text not null default 'legacy'
  check (category_source in ('legacy','rule','manual','import'));
alter table public.documents add column category_confidence text not null default 'LOW'
  check (category_confidence in ('HIGH','MEDIUM','LOW'));

update public.documents
set category_key = case lower(category)
  when 'bseb' then 'bseb'
  when 'examination' then 'examination'
  when 'registration' then 'registration'
  when 'student' then 'student'
  when 'admission' then 'admission'
  when 'payment / fee' then 'payment_fee'
  when 'scholarship' then 'scholarship'
  when 'udise' then 'udise'
  when 'school administration' then 'school_administration'
  when 'teacher / staff' then 'teacher_staff'
  when 'attendance' then 'attendance'
  when 'infrastructure' then 'infrastructure'
  when 'building / repair' then 'building_repair'
  when 'inspection' then 'inspection'
  when 'meeting' then 'meeting'
  when 'training' then 'training'
  when 'government order' then 'government_order'
  when 'district office' then 'district_office'
  when 'block office' then 'block_office'
  when 'notice / circular' then 'notice_circular'
  when 'academic' then 'academic'
  when 'computer science' then 'computer_science'
  when 'data submission' then 'data_submission'
  when 'portal / technical issue' then 'portal_technical'
  when 'deadline / urgent action' then 'deadline_urgent'
  when 'finance / accounts' then 'finance_accounts'
  when 'procurement' then 'procurement'
  when 'general information' then 'general_information'
  else 'other'
end;

alter table public.documents alter column category_key set default 'other';
alter table public.documents alter column category_key set not null;
alter table public.documents add constraint documents_category_key_fk
  foreign key (category_key) references public.document_categories(category_key)
  deferrable initially deferred;

create index documents_category_key_idx on public.documents (category_key);

alter table public.documents add column search_vector tsvector
generated always as (
  to_tsvector('simple'::regconfig,
    coalesce(subject,'') || ' ' ||
    coalesce(short_description,'') || ' ' ||
    coalesce(detailed_summary,'') || ' ' ||
    coalesce(issuing_authority,'') || ' ' ||
    coalesce(reference_number,'') || ' ' ||
    coalesce(required_action,'') || ' ' ||
    coalesce(category,'') || ' ' ||
    coalesce(original_filename,'') || ' ' ||
    coalesce(display_filename,'')
  )
) stored;

create index documents_search_vector_idx on public.documents using gin (search_vector);

drop view public.approved_public_documents;
create view public.approved_public_documents
with (security_invoker = true)
as
select
  d.id,
  d.reference_number,
  d.normalized_issue_date as issue_date,
  d.issuing_authority,
  d.subject,
  d.short_description,
  d.category_key,
  coalesce(c.display_name, d.category) as category,
  d.category as original_category,
  coalesce(c.aliases, '{}'::text[]) as category_aliases,
  d.priority,
  d.required_action,
  d.normalized_deadline as deadline,
  d.public_file_url,
  d.published_at,
  concat_ws(' ',
    d.subject,
    d.short_description,
    d.issuing_authority,
    d.reference_number,
    d.required_action,
    d.category,
    c.display_name,
    array_to_string(c.aliases, ' '),
    array_to_string(c.office_terms, ' '),
    array_to_string(c.content_terms, ' ')
  ) as search_text
from public.documents d
left join public.document_category_definitions c
  on c.category_key = d.category_key
  and c.valid_to is null
where d.approved_for_publication
  and not d.sensitive
  and not d.duplicate;

revoke all on public.document_categories, public.document_category_definitions from anon, authenticated;
grant select on public.document_categories to authenticated;
grant select on public.document_category_definitions to anon;
grant select, insert, update on public.document_category_definitions to authenticated;
grant usage, select on sequence public.document_category_definitions_id_seq to authenticated;
grant select on public.approved_public_documents to anon;
grant select, update on public.documents to authenticated;

commit;
