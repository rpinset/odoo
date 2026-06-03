import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { useLayoutEffect } from "@web/owl2/utils";

export class OfflinePrefetchSystray extends Component {
    static template = "web.OfflinePrefetchSystray";
    static components = { Dropdown };
    static props = {};

    setup() {
        this.offline = useService("offline");
        this.offlinePrefetch = useService("offline_prefetch");
        this.state = useState({
            categories: [],
            categoryIds: [],
            hours: 2,
            scope: "me",
            loading: true,
        });
        onWillStart(async () => {
            const [categories, preferences] = await Promise.all([
                this.offlinePrefetch.getCategories(),
                this.offlinePrefetch.getPreferences(),
            ]);
            this.state.categories = categories;
            this.state.hours = preferences.hours;
            this.state.scope = preferences.scope;
            this.state.categoryIds = preferences.category_ids?.length
                ? preferences.category_ids
                : categories.map((c) => c.id);
            this.state.loading = false;
        });
        useLayoutEffect(this.env.redrawNavbar, () => [
            this.offline.offline,
            this.offlinePrefetch.state.collecting,
        ]);
    }

    get visible() {
        return !this.offline.offline && !this.state.loading;
    }

    onToggleCategory(categoryId, ev) {
        if (ev.target.checked) {
            if (!this.state.categoryIds.includes(categoryId)) {
                this.state.categoryIds.push(categoryId);
            }
        } else {
            this.state.categoryIds = this.state.categoryIds.filter((id) => id !== categoryId);
        }
    }

    isCategoryChecked(categoryId) {
        return this.state.categoryIds.includes(categoryId);
    }

    async onCollect() {
        if (!this.state.categoryIds.length) {
            return;
        }
        await this.offlinePrefetch.collect({
            categoryIds: [...this.state.categoryIds],
            hours: this.state.hours,
            scope: this.state.scope,
        });
    }
}

const systrayItem = {
    Component: OfflinePrefetchSystray,
};

registry.category("systray").add("offline_prefetch", systrayItem, { sequence: 999 });
