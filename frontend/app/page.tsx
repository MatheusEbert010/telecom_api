import { TelecomConsole } from "@/components/telecom-console";
import { getApiBaseUrl } from "@/lib/api";

export default function Page() {
  return <TelecomConsole apiBaseUrl={getApiBaseUrl()} />;
}
