"use client";

import { DatavizCallout } from "@/components/callouts/import-data";
import { DatePickerWithRange } from "@/components/date-range";
import FilterComponent from "@/components/filters";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { useUser } from "@propelauth/nextjs/client";
import {
  ChevronDown,
  Code,
  Flag,
  List,
  MessagesSquare,
  TextSearch,
} from "lucide-react";
import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import useSWR from "swr";

const MetadataForm: React.FC<{}> = ({}) => {
  // create a page with 2 dropdowns :
  // 1. Metric: count of tasks, avg session length, sum of a metadata field,
  // 2. Groupby field : None ; metadataField (user_id, version_id, etc. ) ; event_name ; flag

  // The data is fetched and then displayed as a bar chart or a table

  const { toast } = useToast();

  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);
  const selectedProject = dataStateStore((state) => state.selectedProject);

  const selectedMetric = navigationStateStore((state) => state.selectedMetric);
  const selectedMetricMetadata = navigationStateStore(
    (state) => state.selectedMetricMetadata,
  );
  const selectedGroupBy = navigationStateStore(
    (state) => state.selectedGroupBy,
  );
  const setSelectedMetric = navigationStateStore(
    (state) => state.setSelectedMetric,
  );
  const setSelectedMetricMetadata = navigationStateStore(
    (state) => state.setSelectedMetricMetadata,
  );
  const setSelectedGroupBy = navigationStateStore(
    (state) => state.setSelectedGroupBy,
  );

  const dataFilters = navigationStateStore((state) => state.dataFilters);

  // Fetch metadata unique metadata fields from the API
  const { data } = useSWR(
    [`/api/metadata/${project_id}/fields`, accessToken],
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    {
      revalidateIfStale: false,
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
    },
  );
  const numberMetadataFields: string[] | undefined = data?.number;
  const categoryMetadataFields: string[] | undefined = data?.string;

  // Fetch aggregated metrics from the API
  const { data: pivotData, isLoading: pivotLoading } = useSWR(
    [
      `/api/metadata/${project_id}/pivot/`,
      accessToken,
      selectedMetric,
      selectedMetricMetadata,
      selectedGroupBy,
      numberMetadataFields,
      categoryMetadataFields,
      JSON.stringify(dataFilters),
    ],
    ([url, accessToken]) =>
      authFetcher(url, accessToken, "POST", {
        metric: selectedMetric,
        metric_metadata: selectedMetricMetadata,
        breakdown_by: selectedGroupBy,
        number_metadata_fields: numberMetadataFields,
        category_metadata_fields: categoryMetadataFields,
        filters: dataFilters,
      }).then((response) => {
        return response?.pivot_table;
      }),
    {
      keepPreviousData: true,
    },
  );

  const graphColors = [
    "#22c55e",
    "#ff7c7c",
    "#ffbb43",
    "#4a90e2",
    "#a259ff",
    "#FFDE82",
    "#CBA74E",
    "#917319",
    "#E2E3D8",
    "#68EDCB",
    "#00C4FF",
    "#9FAFA1",
    "#EB6D00",
    "#D3D663",
    "#92CF56",
    "#FFDE82",
    "#FA003C",
    "#9FA8DF",
    "#005400",
    "#505C8D",
  ];
  const isStacked = pivotData?.length > 1 && "stack" in pivotData[0];

  return (
    <>
      <div className="flex flex-col space-y-2">
        <DatavizCallout />
        <div className="flex flex-row space-x-2 items-center">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Metric: {selectedMetric} {selectedMetricMetadata ?? ""}{" "}
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Nb tasks");
                  setSelectedMetricMetadata(null);
                }}
              >
                <MessagesSquare className="h-4 w-4 mr-2" />
                Tasks count
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Event count");
                  setSelectedMetricMetadata(null);
                }}
              >
                <TextSearch className="h-4 w-4 mr-2" />
                Event count
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Event distribution");
                  setSelectedMetricMetadata(null);
                }}
              >
                <TextSearch className="h-4 w-4 mr-2" />
                Event distribution
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Avg Success rate");
                  setSelectedMetricMetadata(null);
                }}
              >
                <Flag className="h-4 w-4 mr-2" />
                Success rate
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedMetric("Avg session length");
                  setSelectedMetricMetadata(null);
                }}
              >
                <List className="h-4 w-4 mr-2" />
                Avg session length
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Code className="h-4 w-4 mr-2" />
                  Avg of metadata
                </DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    {numberMetadataFields?.length === 0 && (
                      <DropdownMenuItem disabled>
                        No numeric metadata found
                      </DropdownMenuItem>
                    )}
                    {numberMetadataFields?.map((field) => (
                      // TODO : Add a way to indicate this is a sum
                      <DropdownMenuItem
                        key={field}
                        onClick={() => {
                          setSelectedMetric("Avg");
                          setSelectedMetricMetadata(field);
                        }}
                      >
                        {`${field}_avg`}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Code className="h-4 w-4 mr-2" />
                  Sum of metadata
                </DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    {numberMetadataFields?.length === 0 && (
                      <DropdownMenuItem disabled>
                        No numeric metadata found
                      </DropdownMenuItem>
                    )}
                    {numberMetadataFields?.map((field) => (
                      // TODO : Add a way to indicate this is a sum
                      <DropdownMenuItem
                        onClick={() => {
                          setSelectedMetric("Sum");
                          setSelectedMetricMetadata(field);
                        }}
                        key={`${field}_sum`}
                      >
                        {field}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
            </DropdownMenuContent>
          </DropdownMenu>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                Breakdown by: {selectedGroupBy}{" "}
                <ChevronDown className="h-4 w-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("None");
                }}
              >
                None
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("event_name");
                }}
              >
                <TextSearch className="h-4 w-4 mr-2" />
                Event name
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("flag");
                }}
              >
                <Flag className="h-4 w-4 mr-2" />
                Eval
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  setSelectedGroupBy("task_position");
                }}
              >
                <List className="h-4 w-4 mr-2" />
                Task position
              </DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Code className="h-4 w-4 mr-2" />
                  Metadata
                </DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    {categoryMetadataFields?.length === 0 && (
                      <DropdownMenuItem disabled>
                        No categorical metadata found
                      </DropdownMenuItem>
                    )}
                    {categoryMetadataFields?.map((field) => (
                      <DropdownMenuItem
                        onClick={() => setSelectedGroupBy(field)}
                        key={`${field}_metadata`}
                      >
                        {field}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <div className="flex flex-row space-x-2 items-center">
          <DatePickerWithRange />
          <FilterComponent variant="tasks" />
        </div>
      </div>
      <div className="w-full h-screen max-h-3/4">
        {!pivotData && pivotLoading && <p>Loading...</p>}
        {(pivotData === null || pivotData?.length == 0) && (
          <p>No data matching your query</p>
        )}
        {pivotData?.length == 1 && (
          <>
            <Card>
              <CardHeader>
                <CardTitle className="text-xl font-light tracking-tight">
                  Breakdown by {selectedGroupBy}:{" "}
                  {pivotData["breakdown_by"] ?? "None"}
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xl font-extrabold">
                <p>
                  {Math.round(
                    pivotData[0][
                      `${selectedMetric}${selectedMetricMetadata ?? ""}`
                    ] * 10000,
                  ) / 10000}
                </p>
              </CardContent>
            </Card>
          </>
        )}
        {pivotData?.length > 1 && (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={pivotData}
              layout="vertical"
              margin={{
                top: 20,
                right: 100,
                bottom: 20,
                left: 100,
              }}
            >
              <CartesianGrid />
              <Tooltip
                formatter={(value) => {
                  if (typeof value === "string") return value;
                  if (typeof value === "number")
                    return `${Math.round(value * 100) / 100}`;
                }}
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="bg-primary shadow-md p-2 rounded-md space-y-1">
                        <div className="text-secondary font-semibold">{`${selectedGroupBy}: ${label}`}</div>
                        <div>
                          {payload.map((item: any) => {
                            const itemName = item.name.split(".")[1]
                              ? item.name.split(".")[1]
                              : item.name;
                            const formatedValue =
                              typeof item.value === "number"
                                ? Math.round(item.value * 1000) / 1000
                                : item.value;

                            // Get the color of the bar
                            let index = 0;
                            if (isStacked) {
                              // use Object.keys(selectedProject?.settings?.events to get the index color
                              index = Object.keys(
                                selectedProject?.settings?.events ?? {},
                              ).indexOf(item.name.split(".")[1]);
                            }
                            const color =
                              graphColors[index % graphColors.length];

                            return (
                              <div className="flex flex-row space-x-2 items-center">
                                <div
                                  className="w-4 h-4"
                                  style={{ backgroundColor: color }}
                                ></div>
                                <div key={item.name} className="text-secondary">
                                  {itemName}: {formatedValue}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  }
                }}
              />
              <YAxis
                dataKey={"breakdown_by"}
                stroke="#888888"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                type="category"
                tickFormatter={(value: any) => {
                  // if value is a string and is too long, truncate it
                  if (typeof value === "string" && value.length > 30) {
                    return value.slice(0, 30) + "...";
                  }
                  return value;
                }}
                width={150}
              />
              <XAxis
                stroke="#888888"
                fontSize={12}
                type="number"
                domain={[0, "dataMax + 1"]}
                // tickLine={false}
                // axisLine={false}
                tickFormatter={(value) => `${Math.round(value * 100) / 100}`}
              />
              {!isStacked && (
                <Bar
                  dataKey={"metric"}
                  fill="#22c55e"
                  stackId="a"
                  // radius={[0, 20, 20, 0]}
                  onClick={(data) => {
                    // Copy the Y value to the clipboard
                    navigator.clipboard.writeText(data["_id"]);
                    toast({
                      title: "Copied to clipboard",
                      description: data["_id"],
                    });
                  }}
                />
              )}
              {isStacked &&
                // Loop over the keys of the dict and create a bar for each key
                Object.keys(selectedProject?.settings?.events ?? {}).map(
                  (key, index) => {
                    console.log(
                      "TEST ",
                      key,
                      index,
                      graphColors[index % graphColors.length],
                    );
                    return (
                      <Bar
                        key={key}
                        dataKey={`stack.${key}`}
                        fill={graphColors[index % graphColors.length]}
                        stackId="a"
                        // radius={[0, 20, 20, 0]}
                        onClick={(data) => {
                          // Copy the Y value to the clipboard
                          navigator.clipboard.writeText(data["_id"]);
                          toast({
                            title: "Copied to clipboard",
                            description: data["_id"],
                          });
                        }}
                      />
                    );
                  },
                )}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </>
  );
};

export default MetadataForm;
