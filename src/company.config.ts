import type { LocalizedText } from "./i18n";
import type { WorkflowStatus } from "./game/workflow";

/**
 * Product names, UI copy, and colors are managed only in this file.
 * Localized values must include all five languages or compilation fails.
 * Product names are not translated, but employee names, alongside their titles, use names natural to each locale.
 */
export const COMPANY = {
  name: "Bang Heri AI Agency",
  mark: "BH",
  pageTitle: {
    ko: "Bang Heri AI Office",
    en: "Bang Heri AI Office",
    zh: "Bang Heri AI Office",
    vi: "Bang Heri AI Office",
    id: "Bang Heri AI Office",
  },
  description: {
    ko: "자율 AI 콘텐츠 제작 오피스",
    en: "Autonomous AI content production office",
    zh: "自主 AI 内容制作办公室",
    vi: "Văn phòng sản xuất nội dung AI tự trị",
    id: "Kantor produksi konten AI otonom",
  },
  tagline: {
    ko: "Kantor AI Otonom — Lombok, NTB",
    en: "Kantor AI Otonom — Lombok, NTB",
    zh: "Kantor AI Otonom — Lombok, NTB",
    vi: "Kantor AI Otonom — Lombok, NTB",
    id: "Kantor AI Otonom — Lombok, NTB",
  },
} as const satisfies {
  name: string;
  mark: string;
  pageTitle: LocalizedText;
  description: LocalizedText;
  tagline: LocalizedText;
};

/** UI colors are passed from the configuration as CSS variables. */
export const THEME = {
  app: "#0b1722",
  frame: "#fffaf0",
  panel: "#eef7f3",
  surface: "#dff1ec",
  line: "#afc9c1",
  edge: "#315f70",
  floor: "#fff0cd",
  cream: "#fffdf5",
  ink: "#102b38",
  muted: "#4a6872",
  skin: "#e0ab84",
  wood: "#b66f3e",
  woodDark: "#694229",
  screen: "#164761",
  green: "#55c985",
  amber: "#f3ad32",
  red: "#c63c47",
  focus: "#176bc1",
  shadow: "#05131c",
} as const;

export const WORKSPACES = [
  {
    id: "agen-bangheri",
    code: "01",
    name: {
      ko: "Chief of Staff",
      en: "Chief of Staff",
      zh: "Chief of Staff",
      vi: "Chief of Staff",
      id: "Chief of Staff",
    },
    role: {
      ko: "Orchestrator",
      en: "Orchestrator",
      zh: "Orchestrator",
      vi: "Orchestrator",
      id: "Orchestrator",
    },
    worker: {
      id: "bangheri",
      title: {
        ko: "Bang Heri",
        en: "Bang Heri",
        zh: "Bang Heri",
        vi: "Bang Heri",
        id: "Bang Heri",
      },
      name: {
        ko: "Bang Heri",
        en: "Bang Heri",
        zh: "Bang Heri",
        vi: "Bang Heri",
        id: "Bang Heri",
      },
      sprite: 0,
    },
    staff: [
      {
        id: "agen-bangheri-staff-1",
        title: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        name: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        sprite: 0,
      },
      {
        id: "agen-bangheri-staff-2",
        title: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        name: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        sprite: 2,
      },
      {
        id: "agen-bangheri-staff-3",
        title: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        name: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        sprite: 4,
      },
    ],
    accent: "#6366f1",
  },
  {
    id: "agen-inbox",
    code: "02",
    name: {
      ko: "Inbox Manager",
      en: "Inbox Manager",
      zh: "Inbox Manager",
      vi: "Inbox Manager",
      id: "Inbox Manager",
    },
    role: {
      ko: "Email & Lead",
      en: "Email & Lead",
      zh: "Email & Lead",
      vi: "Email & Lead",
      id: "Email & Lead",
    },
    worker: {
      id: "inbox",
      title: {
        ko: "Agen Inbox",
        en: "Agen Inbox",
        zh: "Agen Inbox",
        vi: "Agen Inbox",
        id: "Agen Inbox",
      },
      name: {
        ko: "Agen Inbox",
        en: "Agen Inbox",
        zh: "Agen Inbox",
        vi: "Agen Inbox",
        id: "Agen Inbox",
      },
      sprite: 1,
    },
    staff: [
      {
        id: "agen-inbox-staff-1",
        title: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        name: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        sprite: 3,
      },
      {
        id: "agen-inbox-staff-2",
        title: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        name: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        sprite: 5,
      },
      {
        id: "agen-inbox-staff-3",
        title: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        name: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        sprite: 1,
      },
      {
        id: "agen-inbox-staff-4",
        title: { ko: "Staff 4", en: "Staff 4", zh: "Staff 4", vi: "Staff 4", id: "Staff 4" },
        name: { ko: "Staff 4", en: "Staff 4", zh: "Staff 4", vi: "Staff 4", id: "Staff 4" },
        sprite: 0,
      },
    ],
    accent: "#10b981",
  },
  {
    id: "agen-content",
    code: "03",
    name: {
      ko: "Content Studio",
      en: "Content Studio",
      zh: "Content Studio",
      vi: "Content Studio",
      id: "Content Studio",
    },
    role: {
      ko: "Content Strategist",
      en: "Content Strategist",
      zh: "Content Strategist",
      vi: "Content Strategist",
      id: "Content Strategist",
    },
    worker: {
      id: "content",
      title: {
        ko: "Agen Content",
        en: "Agen Content",
        zh: "Agen Content",
        vi: "Agen Content",
        id: "Agen Content",
      },
      name: {
        ko: "Agen Content",
        en: "Agen Content",
        zh: "Agen Content",
        vi: "Agen Content",
        id: "Agen Content",
      },
      sprite: 2,
    },
    staff: [
      {
        id: "agen-content-staff-1",
        title: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        name: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        sprite: 4,
      },
      {
        id: "agen-content-staff-2",
        title: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        name: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        sprite: 1,
      },
      {
        id: "agen-content-staff-3",
        title: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        name: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        sprite: 3,
      },
      {
        id: "agen-content-staff-4",
        title: { ko: "Staff 4", en: "Staff 4", zh: "Staff 4", vi: "Staff 4", id: "Staff 4" },
        name: { ko: "Staff 4", en: "Staff 4", zh: "Staff 4", vi: "Staff 4", id: "Staff 4" },
        sprite: 5,
      },
    ],
    accent: "#3b82f6",
  },
  {
    id: "agen-pm",
    code: "04",
    name: {
      ko: "Project Room",
      en: "Project Room",
      zh: "Project Room",
      vi: "Project Room",
      id: "Project Room",
    },
    role: {
      ko: "Project Manager",
      en: "Project Manager",
      zh: "Project Manager",
      vi: "Project Manager",
      id: "Project Manager",
    },
    worker: {
      id: "pm",
      title: {
        ko: "Agen PM",
        en: "Agen PM",
        zh: "Agen PM",
        vi: "Agen PM",
        id: "Agen PM",
      },
      name: {
        ko: "Agen PM",
        en: "Agen PM",
        zh: "Agen PM",
        vi: "Agen PM",
        id: "Agen PM",
      },
      sprite: 3,
    },
    staff: [
      {
        id: "agen-pm-staff-1",
        title: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        name: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        sprite: 5,
      },
      {
        id: "agen-pm-staff-2",
        title: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        name: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        sprite: 0,
      },
      {
        id: "agen-pm-staff-3",
        title: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        name: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        sprite: 2,
      },
    ],
    accent: "#a855f7",
  },
  {
    id: "agen-admin",
    code: "05",
    name: {
      ko: "Finance & Admin",
      en: "Finance & Admin",
      zh: "Finance & Admin",
      vi: "Finance & Admin",
      id: "Finance & Admin",
    },
    role: {
      ko: "Admin & Finance",
      en: "Admin & Finance",
      zh: "Admin & Finance",
      vi: "Admin & Finance",
      id: "Admin & Finance",
    },
    worker: {
      id: "admin",
      title: {
        ko: "Agen Admin",
        en: "Agen Admin",
        zh: "Agen Admin",
        vi: "Agen Admin",
        id: "Agen Admin",
      },
      name: {
        ko: "Agen Admin",
        en: "Agen Admin",
        zh: "Agen Admin",
        vi: "Agen Admin",
        id: "Agen Admin",
      },
      sprite: 4,
    },
    staff: [
      {
        id: "agen-admin-staff-1",
        title: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        name: { ko: "Staff 1", en: "Staff 1", zh: "Staff 1", vi: "Staff 1", id: "Staff 1" },
        sprite: 1,
      },
      {
        id: "agen-admin-staff-2",
        title: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        name: { ko: "Staff 2", en: "Staff 2", zh: "Staff 2", vi: "Staff 2", id: "Staff 2" },
        sprite: 3,
      },
      {
        id: "agen-admin-staff-3",
        title: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        name: { ko: "Staff 3", en: "Staff 3", zh: "Staff 3", vi: "Staff 3", id: "Staff 3" },
        sprite: 5,
      },
      {
        id: "agen-admin-staff-4",
        title: { ko: "Staff 4", en: "Staff 4", zh: "Staff 4", vi: "Staff 4", id: "Staff 4" },
        name: { ko: "Staff 4", en: "Staff 4", zh: "Staff 4", vi: "Staff 4", id: "Staff 4" },
        sprite: 0,
      },
    ],
    accent: "#f59e0b",
  },
] as const satisfies readonly {
  id: string;
  code: string;
  name: LocalizedText;
  role: LocalizedText;
  worker: { id: string; title: LocalizedText; name: LocalizedText; sprite: number };
  staff: readonly { id: string; title: LocalizedText; name: LocalizedText; sprite: number }[];
  accent: string;
}[];

export type WorkspaceId = (typeof WORKSPACES)[number]["id"];

export const STATUS_LABELS = {
  idle: { ko: "대기", en: "Idle", zh: "待机", vi: "Chờ", id: "Menunggu" },
  running: { ko: "실행 중", en: "Running", zh: "运行中", vi: "Đang chạy", id: "Berjalan" },
  awaiting_approval: { ko: "승인 대기", en: "Awaiting approval", zh: "待审批", vi: "Chờ duyệt", id: "Menunggu persetujuan" },
  completed: { ko: "완료", en: "Done", zh: "完成", vi: "Xong", id: "Selesai" },
  failed: { ko: "실패", en: "Failed", zh: "失败", vi: "Thất bại", id: "Gagal" },
} as const satisfies Record<WorkflowStatus, LocalizedText>;
