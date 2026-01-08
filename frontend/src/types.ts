export interface Tag {
    label: string;
    color: "purple" | "blue" | "gray" | "red" | string;
}

export interface IntelItem {
    id: string;
    title: string;
    summary: string;
    content?: string;
    source: string;
    url?: string;
    time: string;
    timestamp: number;
    tags: Tag[];
    favorited: boolean;
}

export interface IntelListResponse {
    items: IntelItem[];
    total: number;
}

export interface AgentSearchResponse {
    sources: IntelItem[];
    answer?: string;
}

export type SearchType = "hot" | "history" | "all";
export type TimeRange = "all" | "3h" | "6h" | "12h";
