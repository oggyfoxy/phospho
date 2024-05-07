"use client";

import ComingSoonAlert from "@/components/coming-soon";
import { DatePickerWithRange } from "@/components/date-range";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import {
  CustomDateRange,
  DetectionEngine,
  DetectionScope,
  EventDefinition,
} from "@/models/models";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import { QuestionMarkIcon } from "@radix-ui/react-icons";
import Link from "next/link";
import { useForm } from "react-hook-form";
import useSWR, { useSWRConfig } from "swr";
import { z } from "zod";

export default function RunEvent({
  setOpen,
  eventToRun,
}: {
  setOpen: (open: boolean) => void;
  eventToRun: EventDefinition;
}) {
  // This is a form that lets you run an event detection on previous data
  // Component to create an event or edit an existing event

  const project_id = navigationStateStore((state) => state.project_id);
  const orgMetadata = dataStateStore((state) => state.selectedOrgMetadata);
  const selectedProject = dataStateStore((state) => state.selectedProject);
  const { mutate } = useSWRConfig();
  const { loading, accessToken } = useUser();
  const { toast } = useToast();
  const dateRange = navigationStateStore((state) => state.dateRange);

  const { data: totalNbTasksData } = useSWR(
    [
      `/api/explore/${project_id}/aggregated/tasks`,
      accessToken,
      JSON.stringify(dateRange),
      "total_nb_tasks",
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metrics: ["total_nb_tasks"],
        tasks_filter: {
          created_at_start: dateRange?.created_at_start,
          created_at_end: dateRange?.created_at_end,
        },
      }),
    {
      keepPreviousData: true,
    },
  );
  const totalNbTasks: number | null | undefined =
    totalNbTasksData?.total_nb_tasks;

  const formSchema = z.object({
    sample_rate: z.coerce.number().min(0).max(1),
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      sample_rate: 1,
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    console.log("Submitting event:", values);
    if (!selectedProject) {
      console.log("Submit: No selected project");
      return;
    }
    if (!selectedProject.settings) {
      console.log("Submit: No selected project settings");
      return;
    }
  }

  return (
    <>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="font-normal space-y-4"
          key={`createEventForm_${eventToRun.id}`}
        >
          <SheetHeader>
            <SheetTitle className="text-xl">
              Detect event "{eventToRun.event_name}" on past data
            </SheetTitle>
            <SheetDescription>
              Detect if this event happened on a sample of previously logged
              data.
            </SheetDescription>
          </SheetHeader>
          <Separator />
          <div className="flex-col space-y-4">
            <FormItem>
              <FormLabel>Date range</FormLabel>
              <DatePickerWithRange />
            </FormItem>
            <FormField
              control={form.control}
              name="sample_rate"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Sample rate</FormLabel>
                  <FormControl>
                    <Input
                      className="w-32"
                      placeholder="0.0 - 1.0"
                      defaultValue={1}
                      min={0}
                      max={1}
                      step={0.01}
                      type="number"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {totalNbTasks === undefined && <>Loading...</>}
            {totalNbTasks !== undefined &&
              totalNbTasks !== null &&
              totalNbTasks > 0 && (
                <div className="flex flex-row space-x-1 items-center">
                  This will run event detection on:{" "}
                  <span className="font-semibold ml-1">
                    {Math.floor(totalNbTasks * form.getValues("sample_rate"))}{" "}
                    tasks
                  </span>
                  <HoverCard openDelay={50} closeDelay={50}>
                    <HoverCardTrigger>
                      <QuestionMarkIcon className="h-4 w-4 rounded-full bg-primary text-secondary p-0.5" />
                    </HoverCardTrigger>
                    <HoverCardContent className="w-72">
                      You are billed based on the number of detections.{" "}
                      <Link
                        href="https://docs.phospho.ai/guides/events"
                        target="_blank"
                        className="underline"
                      >
                        Learn more
                      </Link>
                    </HoverCardContent>
                  </HoverCard>
                </div>
              )}
            {(totalNbTasks === 0 || totalNbTasks === null) && (
              <div>No task found in this date range.</div>
            )}
          </div>
          <SheetFooter>
            <Button
              type="submit"
              disabled={
                loading || totalNbTasks === undefined || totalNbTasks === 0
              }
            >
              Run detection
            </Button>
          </SheetFooter>
        </form>
      </Form>
    </>
  );
}
