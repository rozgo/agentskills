# Advanced Patterns Reference

## Table of Contents
- [Islands Architecture](#islands-architecture)
- [Directives](#directives)
- [Slots](#slots)
- [Spread Syntax](#spread-syntax)
- [Builder Syntax](#builder-syntax)
- [Callbacks](#callbacks)
- [Triggers](#triggers)

## Islands Architecture

Islands mode hydrates only interactive components, reducing JS bundle size.

### Enabling Islands

```toml
[features]
islands = ["leptos/islands"]
```

### Defining Islands

```rust
use leptos::prelude::*;

// Static component - never hydrated
#[component]
fn StaticHeader() -> impl IntoView {
    view! {
        <header>
            <h1>"My Site"</h1>
            <nav>"Navigation..."</nav>
        </header>
    }
}

// Island - hydrated with interactivity
#[island]
fn Counter() -> impl IntoView {
    let count = RwSignal::new(0);

    view! {
        <button on:click=move |_| count.update(|n| *n += 1)>
            "Count: " {count}
        </button>
    }
}

#[component]
fn App() -> impl IntoView {
    view! {
        <StaticHeader />        // No JS needed
        <main>
            <p>"Static content..."</p>
            <Counter />         // Only this gets hydrated
        </main>
    }
}
```

### Nested Islands

Context flows through island boundaries:

```rust
#[island]
fn OuterIsland(children: Children) -> impl IntoView {
    provide_context(42i32);

    view! {
        <div class="outer">
            {children()}
        </div>
    }
}

#[island]
fn InnerIsland() -> impl IntoView {
    let value = use_context::<i32>();

    view! {
        <p>"Context value: " {value}</p>
    }
}

// Usage
view! {
    <OuterIsland>
        <InnerIsland />
    </OuterIsland>
}
```

## Directives

Directives add behavior to elements via `use:directive` syntax.

### Defining Directives

```rust
use leptos::prelude::*;
use leptos::tachys::html::element::Element;

// Simple directive (no params)
pub fn focus_on_mount(el: Element) {
    // el is the DOM element
    request_animation_frame(move || {
        let _ = el.focus();
    });
}

// Directive with value
pub fn highlight(el: Element, color: &str) {
    let color = color.to_owned();
    el.set_attribute("style", &format!("background-color: {color}"));
}

// Directive with cleanup
pub fn click_outside(el: Element, handler: impl Fn() + 'static) {
    let handler = std::rc::Rc::new(handler);
    let el_clone = el.clone();

    let listener = Closure::wrap(Box::new(move |ev: web_sys::MouseEvent| {
        if let Some(target) = ev.target() {
            if !el_clone.contains(Some(&target.unchecked_into())) {
                (handler)();
            }
        }
    }) as Box<dyn Fn(_)>);

    document()
        .add_event_listener_with_callback("click", listener.as_ref().unchecked_ref())
        .unwrap();

    on_cleanup(move || {
        let _ = document()
            .remove_event_listener_with_callback("click", listener.as_ref().unchecked_ref());
    });
}
```

### Using Directives

```rust
view! {
    // No value
    <input type="text" use:focus_on_mount />

    // With value
    <div use:highlight="yellow">"Highlighted"</div>

    // With closure
    <div use:click_outside=move || modal_open.set(false)>
        "Modal content"
    </div>
}
```

## Slots

Slots allow named content injection into components.

### Defining Slots

```rust
use leptos::prelude::*;

#[slot]
struct Header {
    children: Children,
}

#[slot]
struct Footer {
    children: Children,
}

#[component]
fn Card(
    header: Header,
    #[prop(optional)] footer: Option<Footer>,
    children: Children,
) -> impl IntoView {
    view! {
        <div class="card">
            <div class="card-header">
                {(header.children)()}
            </div>
            <div class="card-body">
                {children()}
            </div>
            {footer.map(|f| view! {
                <div class="card-footer">
                    {(f.children)()}
                </div>
            })}
        </div>
    }
}
```

### Using Slots

```rust
view! {
    <Card>
        <Header slot>"Card Title"</Header>
        <p>"Card body content"</p>
        <Footer slot>
            <button>"Action"</button>
        </Footer>
    </Card>
}
```

### Conditional Slots

```rust
#[slot]
struct Then {
    children: ChildrenFn,
}

#[slot]
struct Else {
    children: ChildrenFn,
}

#[component]
fn If(
    when: Signal<bool>,
    then: Then,
    #[prop(optional)] else_: Option<Else>,
) -> impl IntoView {
    move || {
        if when.get() {
            (then.children)().into_any()
        } else if let Some(else_) = &else_ {
            (else_.children)().into_any()
        } else {
            ().into_any()
        }
    }
}
```

## Spread Syntax

Spread attributes and event handlers across elements.

### Collecting Attributes

```rust
// Create spreadable attributes
let attrs = view! { <{..} class="btn" id="my-btn" /> };
let handlers = view! { <{..} on:click=move |_| log!("clicked") /> };

// Apply to elements
view! {
    <button {..attrs} {..handlers}>"Click me"</button>
}
```

### Component Spread

```rust
#[component]
fn Button(
    #[prop(attrs)] attrs: Vec<(&'static str, Attribute)>,
    children: Children,
) -> impl IntoView {
    view! {
        <button {..attrs}>
            {children()}
        </button>
    }
}

// Usage
let my_attrs = view! { <{..} class="primary" disabled=true /> };
view! {
    <Button {..my_attrs}>"Submit"</Button>
}
```

### Merging Attributes

```rust
view! {
    // Attributes merge, later values override
    <div
        class="base"
        {..extra_attrs}  // May add/override class
        id="final"       // Always applied
    >
    </div>
}
```

## Builder Syntax

Build views without macros:

```rust
use leptos::{
    ev,
    html::{button, div, input, p, span},
    prelude::*,
};

pub fn counter(initial: i32) -> impl IntoView {
    let count = RwSignal::new(initial);

    div()
        .class("counter")
        .child((
            button()
                .on(ev::click, move |_| count.update(|n| *n -= 1))
                .child("-1"),
            span()
                .class("count")
                .child(move || count.get()),
            button()
                .on(ev::click, move |_| count.update(|n| *n += 1))
                .child("+1"),
        ))
}
```

### Builder with Conditionals

```rust
fn conditional_content(show: Signal<bool>) -> impl IntoView {
    div().child(
        move || {
            if show.get() {
                p().child("Visible").into_any()
            } else {
                span().child("Hidden").into_any()
            }
        }
    )
}
```

### Builder with Lists

```rust
fn item_list(items: Signal<Vec<String>>) -> impl IntoView {
    ul().child(
        move || {
            items.get()
                .into_iter()
                .map(|item| li().child(item))
                .collect_view()
        }
    )
}
```

## Callbacks

Type-erased `Copy` callbacks for component props:

### Callback Types

```rust
use leptos::prelude::*;

// Callback<In, Out> - Send + Sync
// UnsyncCallback<In, Out> - not Send + Sync (for !Send closures)

#[component]
fn Button(
    #[prop(into)] on_click: Callback<(), ()>,
    #[prop(into, optional)] on_hover: Option<Callback<(), ()>>,
    children: Children,
) -> impl IntoView {
    view! {
        <button
            on:click=move |_| on_click.run(())
            on:mouseenter=move |_| {
                if let Some(cb) = on_hover {
                    cb.run(());
                }
            }
        >
            {children()}
        </button>
    }
}
```

### Creating Callbacks

```rust
// From closure
let handler = Callback::new(|_| log!("clicked"));

// Usage with component
view! {
    <Button on_click=move |_| log!("clicked")>
        "Click"
    </Button>

    <Button on_click=handler on_hover=Some(Callback::new(|_| log!("hover")))>
        "Hover"
    </Button>
}
```

### Callbacks with Values

```rust
#[component]
fn Select<T: Clone + 'static>(
    options: Vec<T>,
    #[prop(into)] on_select: Callback<T, ()>,
    #[prop(into)] render: Callback<T, String>,
) -> impl IntoView {
    view! {
        <select on:change=move |ev| {
            let idx: usize = event_target_value(&ev).parse().unwrap();
            on_select.run(options[idx].clone());
        }>
            {options.iter().enumerate().map(|(i, opt)| {
                view! { <option value=i>{render.run(opt.clone())}</option> }
            }).collect_view()}
        </select>
    }
}
```

## Triggers

Data-less signals for notification only:

```rust
use leptos::prelude::*;

#[component]
fn RefreshableList() -> impl IntoView {
    let refresh = ArcTrigger::new();

    // Resource that refetches when triggered
    let items = Resource::new(
        move || refresh.track(),  // Track the trigger
        |_| fetch_items()
    );

    view! {
        <button on:click=move |_| refresh.notify()>
            "Refresh"
        </button>

        <Suspense fallback=|| "Loading...">
            {move || Suspend::new(async move {
                items.await.map(|list| view! {
                    <ul>
                        {list.into_iter().map(|i| view! { <li>{i}</li> }).collect_view()}
                    </ul>
                })
            })}
        </Suspense>
    }
}
```

### Trigger vs Signal

```rust
// Trigger - no value, just notification
let refresh = ArcTrigger::new();
refresh.notify();  // Notify subscribers
refresh.track();   // Subscribe to notifications

// Signal<()> - similar but carries unit value
let refresh = RwSignal::new(());
refresh.set(());   // Update and notify
refresh.get();     // Read and subscribe
```

Use triggers when:
- You only need to signal "something happened"
- No actual data needs to be passed
- You want semantic clarity (trigger vs value)
