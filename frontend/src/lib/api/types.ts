/** Friendly names for the API types generated in schema.ts (`npm run gen:api`). */
import type { components } from "./schema";

type Schemas = components["schemas"];

export type User = Schemas["UserOut"];
export type Medicine = Schemas["MedicineOut"];
export type MedicineSearchResponse = Schemas["MedicineSearchResponse"];
export type StockSearchResponse = Schemas["SearchResponse"];
export type StockHit = Schemas["SearchHit"];
export type Order = Schemas["OrderOut"];
export type OrderCreate = Schemas["OrderCreate"];
export type OrderStatus = Order["status"];
export type Prescription = Schemas["PrescriptionOut"];
export type UserRegister = Schemas["UserRegister"];
