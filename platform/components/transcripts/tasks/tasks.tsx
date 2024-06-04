"use client";

import { SendDataCallout } from "@/components/callouts/import-data";
import { navigationStateStore } from "@/store/store";
import React from "react";

import TasksDataviz from "./tasks-dataviz";
import { TasksTable } from "./tasks-table";

const Tasks: React.FC = () => {
  const project_id = navigationStateStore((state) => state.project_id);

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      <SendDataCallout />
      <div className="hidden h-full flex-1 flex-col space-y-2 md:flex relative">
        <TasksDataviz />
        <TasksTable />
      </div>
    </>
  );
};

export default Tasks;
