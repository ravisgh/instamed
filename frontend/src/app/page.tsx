import { SearchPage } from "@/components/search/SearchPage";
import { Page } from "@/components/ui";

export default function Home() {
  return (
    <Page title="Find your medicines">
      <SearchPage />
    </Page>
  );
}
