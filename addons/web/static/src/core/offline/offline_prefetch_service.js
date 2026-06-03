import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { parseXML } from "@web/core/utils/xml";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { extractFieldsFromArchInfo, getFieldsSpec } from "@web/model/relational_model/utils";
import { FormArchParser } from "@web/views/form/form_arch_parser";
import { ListArchParser } from "@web/views/list/list_arch_parser";

const BATCH = 40;

export class OfflinePrefetchService {
    constructor(env, { action, notification, offline, orm, view }) {
        this.env = env;
        this.actionService = action;
        this.notification = notification;
        this.offline = offline;
        this.orm = orm;
        this.viewService = view;
        this.state = {
            collecting: false,
            progress: 0,
            progressLabel: "",
        };
    }

    async getPreferences() {
        return rpc("/web/offline/preferences");
    }

    async getCategories() {
        return rpc("/web/offline/categories");
    }

    async collect({ categoryIds, hours, scope }) {
        if (this.state.collecting) {
            return;
        }
        this.state.collecting = true;
        this.state.progress = 0;
        const closeNotification = this.notification.add(_t("Collecting data for offline use…"), {
            type: "info",
            sticky: true,
        });
        try {
            const result = await rpc("/web/offline/prefetch", {
                category_ids: categoryIds,
                hours,
                scope,
            });
            const jobs = [...result.manifest];
            if (result.partners?.res_ids?.length) {
                jobs.push(result.partners);
            }
            let done = 0;
            const totalSteps = jobs.reduce(
                (acc, job) => acc + 1 + (job.view_types?.includes("form") ? job.res_ids.length : 0),
                0
            );
            const bump = (label) => {
                done += 1;
                this.state.progress = Math.round((done / totalSteps) * 100);
                this.state.progressLabel = label;
            };
            for (const job of jobs) {
                await this._prefetchJob(job, bump);
            }
            this.notification.add(
                _t("Offline data is ready. You can work without a connection and refresh the page."),
                { type: "success" }
            );
            return result;
        } finally {
            this.state.collecting = false;
            closeNotification();
        }
    }

    async _prefetchJob(job, bump) {
        const action = await this.actionService.loadAction(job.action_xmlid);
        const actionId = action.id;
        const context = { ...user.context, ...action.context };
        const viewTypes = job.view_types || ["list", "form"];
        if (viewTypes.includes("list") && job.res_ids.length) {
            await this._prefetchList(job.model, job.res_ids, actionId, context, action);
            bump(_t("List %(model)s", { model: job.model }));
            await this.offline.setAvailableOffline(actionId, "list", {
                search: {
                    key: `prefetch:${job.category_id || job.model}`,
                    domain: [["id", "in", job.res_ids]],
                    context,
                    groupBy: [],
                    orderBy: [],
                },
            });
        }
        if (viewTypes.includes("form")) {
            for (let index = 0; index < job.res_ids.length; index += BATCH) {
                const slice = job.res_ids.slice(index, index + BATCH);
                for (const resId of slice) {
                    await this._prefetchForm(job.model, resId, actionId, context);
                    await this.offline.setAvailableOffline(actionId, "form", { resId });
                    bump(_t("Form %(model)s #%(id)s", { model: job.model, id: resId }));
                }
            }
        }
    }

    async _prefetchList(resModel, resIds, actionId, context, action) {
        const views = action.views || [
            [false, "list"],
            [false, "form"],
        ];
        const listView = views.find((v) => v[1] === "list") || [false, "list"];
        const descriptions = await this.viewService.loadViews(
            { resModel, views: [listView], context },
            { actionId, loadActionMenus: false }
        );
        const archXml = descriptions.views.list?.arch;
        if (!archXml) {
            return;
        }
        const parser = new ListArchParser();
        const archInfo = parser.parse(parseXML(archXml), descriptions.relatedModels, resModel);
        const { activeFields, fields } = extractFieldsFromArchInfo(archInfo, descriptions.fields);
        const specification = getFieldsSpec(activeFields, fields, context);
        await this.orm
            .cache({ type: "disk", update: "always" })
            .webSearchRead(resModel, [["id", "in", resIds]], {
                specification,
                context,
            });
    }

    async _prefetchForm(resModel, resId, actionId, context) {
        const descriptions = await this.viewService.loadViews(
            { resModel, views: [[false, "form"]], context },
            { actionId, loadActionMenus: true }
        );
        const archXml = descriptions.views.form?.arch;
        if (!archXml) {
            return;
        }
        const parser = new FormArchParser();
        const archInfo = parser.parse(parseXML(archXml), descriptions.relatedModels, resModel);
        const { activeFields, fields } = extractFieldsFromArchInfo(archInfo, descriptions.fields);
        const specification = getFieldsSpec(activeFields, fields, context, { withInvisible: true });
        await this.orm.cache({ type: "disk", update: "always" }).webRead(resModel, [resId], {
            specification,
            context,
        });
    }
}

export const offlinePrefetchService = {
    dependencies: ["action", "notification", "offline", "orm", "view"],
    start(env, services) {
        return new OfflinePrefetchService(env, services);
    },
};

registry.category("services").add("offline_prefetch", offlinePrefetchService);
