import { defineStore } from 'pinia';

export interface DataItemType {
	field_name: string;
	is_create: boolean;
	is_query: boolean;
	is_update: boolean;
}
