# SSR/CSR Setup Guide

The definitive guide to structuring a Leptos app that works for both SSR and CSR without warnings.

## The One True Pattern

```
my_app/
├── Cargo.toml          # Features: ssr, hydrate (mutually exclusive)
├── src/
│   ├── lib.rs          # Shared code + hydrate entry point
│   ├── main.rs         # Server entry point (ssr only)
│   └── app.rs          # Components + server functions
```

## Cargo.toml

```toml
[package]
name = "my_app"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "rlib"]

[dependencies]
# Always included
leptos = { version = "0.8" }
serde = { version = "1.0", features = ["derive"] }
wasm-bindgen = "0.2"
console_error_panic_hook = "0.1"

# Server-only deps: MUST be optional
leptos_axum = { version = "0.8", optional = true }
axum = { version = "0.8", optional = true }
tokio = { version = "1", features = ["full"], optional = true }
tower = { version = "0.4", optional = true }
tower-http = { version = "0.5", features = ["fs"], optional = true }
sqlx = { version = "0.8", features = ["runtime-tokio-rustls", "sqlite"], optional = true }

[features]
# CRITICAL: These are mutually exclusive. Never enable both.
hydrate = ["leptos/hydrate"]
ssr = [
  "leptos/ssr",
  "dep:leptos_axum",
  "dep:axum",
  "dep:tokio",
  "dep:tower",
  "dep:tower-http",
  # Add other server deps here
]

# cargo-leptos configuration
[package.metadata.leptos]
output-name = "my_app"
site-root = "target/site"
site-pkg-dir = "pkg"
site-addr = "127.0.0.1:3000"
reload-port = 3001
bin-features = ["ssr"]
bin-default-features = false
lib-features = ["hydrate"]
lib-default-features = false
```

## src/lib.rs

```rust
pub mod app;

// Hydrate entry point - only compiled for WASM
#[cfg(feature = "hydrate")]
#[wasm_bindgen::prelude::wasm_bindgen]
pub fn hydrate() {
    console_error_panic_hook::set_once();
    leptos::mount::hydrate_body(app::App);
}
```

## src/main.rs

```rust
#[cfg(feature = "ssr")]
#[tokio::main]
async fn main() {
    use axum::Router;
    use leptos::prelude::*;
    use leptos_axum::{generate_route_list, LeptosRoutes};
    use my_app::app::*;

    let conf = get_configuration(None).unwrap();
    let leptos_options = conf.leptos_options;
    let addr = leptos_options.site_addr;
    let routes = generate_route_list(App);

    let app = Router::new()
        .leptos_routes(&leptos_options, routes, {
            let leptos_options = leptos_options.clone();
            move || shell(leptos_options.clone())
        })
        .fallback(leptos_axum::file_and_error_handler(shell))
        .with_state(leptos_options);

    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    println!("listening on http://{}", &addr);
    axum::serve(listener, app.into_make_service()).await.unwrap();
}

// Fallback for non-SSR builds (handles cargo check without features)
#[cfg(not(feature = "ssr"))]
fn main() {}
```

## src/app.rs

```rust
use leptos::prelude::*;
use serde::{Deserialize, Serialize};

// Shell for SSR HTML wrapper
pub fn shell(options: LeptosOptions) -> impl IntoView {
    view! {
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1"/>
                <AutoReload options=options.clone() />
                <HydrationScripts options/>
                <link rel="stylesheet" href="/pkg/my_app.css"/>
            </head>
            <body>
                <App/>
            </body>
        </html>
    }
}

// Shared types - work on both client and server
#[derive(Clone, Debug, Serialize, Deserialize)]
#[cfg_attr(feature = "ssr", derive(sqlx::FromRow))]  // Server-only derive
pub struct Todo {
    pub id: i32,
    pub title: String,
    pub completed: bool,
}

// =============================================================================
// SERVER-ONLY MODULE - all server imports go here
// =============================================================================
#[cfg(feature = "ssr")]
pub mod ssr {
    use leptos::prelude::*;
    use sqlx::{Connection, SqliteConnection};

    pub async fn db() -> Result<SqliteConnection, ServerFnError> {
        Ok(SqliteConnection::connect("sqlite:app.db").await?)
    }
}

// =============================================================================
// SERVER FUNCTIONS - import server module INSIDE the function
// =============================================================================
#[server]
pub async fn get_todos() -> Result<Vec<Todo>, ServerFnError> {
    use self::ssr::*;  // Import HERE, not at file top
    let mut conn = db().await?;
    let todos = sqlx::query_as::<_, Todo>("SELECT * FROM todos")
        .fetch_all(&mut conn)
        .await?;
    Ok(todos)
}

#[server]
pub async fn add_todo(title: String) -> Result<(), ServerFnError> {
    use self::ssr::*;
    let mut conn = db().await?;
    sqlx::query("INSERT INTO todos (title, completed) VALUES ($1, false)")
        .bind(title)
        .execute(&mut conn)
        .await?;
    Ok(())
}

// =============================================================================
// COMPONENTS - shared, run on both client and server
// =============================================================================
#[component]
pub fn App() -> impl IntoView {
    view! {
        <main>
            <h1>"My App"</h1>
            <TodoList/>
        </main>
    }
}

#[component]
fn TodoList() -> impl IntoView {
    let add_todo = ServerAction::<AddTodo>::new();
    let todos = Resource::new(
        move || add_todo.version().get(),
        |_| get_todos()
    );

    view! {
        <Suspense fallback=|| "Loading...">
            {move || Suspend::new(async move {
                todos.await.map(|list| {
                    list.into_iter().map(|todo| {
                        view! { <p>{todo.title}</p> }
                    }).collect_view()
                })
            })}
        </Suspense>
    }
}
```

## Build Commands

```bash
# Development (with cargo-leptos)
cargo leptos watch

# Check server code
cargo check --features ssr

# Check client code
cargo check --features hydrate --lib --target wasm32-unknown-unknown

# Production build
cargo leptos build --release
```

## Rules to Avoid Warnings

### 1. Never enable both features together

```bash
# WRONG
cargo check --features ssr,hydrate

# RIGHT - separate commands
cargo check --features ssr
cargo check --features hydrate --lib --target wasm32-unknown-unknown
```

### 2. Server deps must be optional

```toml
# WRONG - compiles for WASM, fails
sqlx = "0.8"

# RIGHT
sqlx = { version = "0.8", optional = true }

[features]
ssr = ["dep:sqlx"]
```

### 3. Server imports inside guarded module or server fn

```rust
// WRONG - warning: unused import on client
use sqlx::*;

#[server]
async fn my_fn() -> Result<(), ServerFnError> { }

// RIGHT - import inside function
#[server]
async fn my_fn() -> Result<(), ServerFnError> {
    use sqlx::*;
}

// OR - guarded module + import in function
#[cfg(feature = "ssr")]
mod ssr {
    pub use sqlx::*;
}

#[server]
async fn my_fn() -> Result<(), ServerFnError> {
    use self::ssr::*;
}
```

### 4. Conditional derives for server-only traits

```rust
#[derive(Clone, Serialize, Deserialize)]
#[cfg_attr(feature = "ssr", derive(sqlx::FromRow))]
pub struct User {
    pub id: i32,
    pub name: String,
}
```

### 5. Browser APIs in Effect or guarded

```rust
// WRONG - panics on server
let width = window().inner_width();

// RIGHT - Effect only runs on client
Effect::new(move |_| {
    let width = window().inner_width();
});

// OR - cfg guard
#[cfg(target_arch = "wasm32")]
let width = window().inner_width().unwrap_or(0);
#[cfg(not(target_arch = "wasm32"))]
let width = 0;
```

## CSR-Only Apps

For client-side only (no server rendering):

```toml
[dependencies]
leptos = { version = "0.8", features = ["csr"] }
```

```rust
fn main() {
    console_error_panic_hook::set_once();
    leptos::mount::mount_to_body(App);
}
```

```bash
trunk serve        # Development
trunk build --release  # Production
```

## Quick Reference

| Task | Command |
|------|---------|
| Dev server | `cargo leptos watch` |
| Check server | `cargo check --features ssr` |
| Check client | `cargo check --features hydrate --lib --target wasm32-unknown-unknown` |
| Build release | `cargo leptos build --release` |
| CSR dev | `trunk serve` |
