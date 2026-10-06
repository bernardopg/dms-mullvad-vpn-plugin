.pragma library
// One engine per plugin version, shared by every bar instance (several screens or bars).
// Plain JS state, so QML bindings never re-evaluate on registration changes, and widgets
// are never written to here: during shell exit they may already be half destroyed.
var engines = {};

function engine(version, create) {
    if (!engines[version])
        engines[version] = create();
    return engines[version];
}

function attach(version, widget) {
    const shared = engines[version];
    shared.users = shared.users.concat([widget]);
    if (!shared.owner)
        shared.owner = widget;
}

function detach(version, widget) {
    const shared = engines[version];
    if (!shared)
        return;
    const users = shared.users.filter(user => user !== widget);
    shared.users = users;
    if (shared.activeWidget === widget)
        shared.activeWidget = null;
    if (shared.owner === widget)
        shared.owner = users[0] || null;
    if (users.length === 0) {
        delete engines[version];
        shared.destroy();
    }
}
