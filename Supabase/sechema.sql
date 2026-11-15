-- Intelligent Student Task Management System: database schema
-- Run in Supabase: SQL Editor -> New query -> paste -> Run

create table if not exists profiles (
    id uuid primary key default gen_random_uuid(),
    full_name text not null,
    email text unique not null,
    commitment_index_score float default 0,
    last_activity timestamptz default now(),
    created_at timestamptz default now()
);

create table if not exists groups (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    description text,
    created_by uuid references profiles(id) on delete set null,
    created_at timestamptz default now()
);

create table if not exists group_members (
    id uuid primary key default gen_random_uuid(),
    group_id uuid not null references groups(id) on delete cascade,
    user_id uuid not null references profiles(id) on delete cascade,
    role text not null default 'member',
    joined_at timestamptz default now(),
    unique (group_id, user_id)
);

create table if not exists tasks (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references profiles(id) on delete cascade,
    group_id uuid references groups(id) on delete set null,
    title text not null,
    description text,
    subject_name text,
    deadline timestamptz,
    subject_importance numeric,
    complexity numeric,
    priority_level numeric,
    status text not null default 'pending',
    created_at timestamptz default now()
);

create table if not exists subtasks (
    id uuid primary key default gen_random_uuid(),
    task_id uuid not null references tasks(id) on delete cascade,
    title text not null,
    estimated_hours numeric,
    is_completed boolean not null default false
);

create table if not exists notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references profiles(id) on delete cascade,
    message text not null,
    type text,
    is_read boolean not null default false,
    created_at timestamptz default now()
);

create index if not exists idx_tasks_user on tasks(user_id);
create index if not exists idx_subtasks_task on subtasks(task_id);
create index if not exists idx_members_user on group_members(user_id);