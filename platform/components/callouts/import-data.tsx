"use client";

import { PasswordInput } from "@/components/password-input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { AlertDialog, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useToast } from "@/components/ui/use-toast";
import { authFetcher } from "@/lib/fetcher";
import { dataStateStore, navigationStateStore } from "@/store/store";
import { zodResolver } from "@hookform/resolvers/zod";
import { useUser } from "@propelauth/nextjs/client";
import {
  BarChartBig,
  CopyIcon,
  Lock,
  Mail,
  MonitorPlay,
  NotebookText,
  Plus,
  Telescope,
  TriangleAlert,
  Upload,
  X,
} from "lucide-react";
import { Unplug } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import React from "react";
import { CopyBlock, dracula } from "react-code-blocks";
import { useForm } from "react-hook-form";
import useSWR, { useSWRConfig } from "swr";
import { z } from "zod";

import UpgradeButton from "../upgrade-button";

const PythonIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 448 512"
      fill="currentColor"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mr-2 w-6 h-6 text-primary"
    >
      <path d="M439.8 200.5c-7.7-30.9-22.3-54.2-53.4-54.2h-40.1v47.4c0 36.8-31.2 67.8-66.8 67.8H172.7c-29.2 0-53.4 25-53.4 54.3v101.8c0 29 25.2 46 53.4 54.3 33.8 9.9 66.3 11.7 106.8 0 26.9-7.8 53.4-23.5 53.4-54.3v-40.7H226.2v-13.6h160.2c31.1 0 42.6-21.7 53.4-54.2 11.2-33.5 10.7-65.7 0-108.6zM286.2 404c11.1 0 20.1 9.1 20.1 20.3 0 11.3-9 20.4-20.1 20.4-11 0-20.1-9.2-20.1-20.4 .1-11.3 9.1-20.3 20.1-20.3zM167.8 248.1h106.8c29.7 0 53.4-24.5 53.4-54.3V91.9c0-29-24.4-50.7-53.4-55.6-35.8-5.9-74.7-5.6-106.8 .1-45.2 8-53.4 24.7-53.4 55.6v40.7h106.9v13.6h-147c-31.1 0-58.3 18.7-66.8 54.2-9.8 40.7-10.2 66.1 0 108.6 7.6 31.6 25.7 54.2 56.8 54.2H101v-48.8c0-35.3 30.5-66.4 66.8-66.4zm-6.7-142.6c-11.1 0-20.1-9.1-20.1-20.3 .1-11.3 9-20.4 20.1-20.4 11 0 20.1 9.2 20.1 20.4s-9 20.3-20.1 20.3z" />
    </svg>
  );
};

const JavaScriptIcon = () => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 448 512"
      fill="currentColor"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mr-2 w-6 h-6 text-primary"
    >
      <path d="M0 32v448h448V32H0zm243.8 349.4c0 43.6-25.6 63.5-62.9 63.5-33.7 0-53.2-17.4-63.2-38.5l34.3-20.7c6.6 11.7 12.6 21.6 27.1 21.6 13.8 0 22.6-5.4 22.6-26.5V237.7h42.1v143.7zm99.6 63.5c-39.1 0-64.4-18.6-76.7-43l34.3-19.8c9 14.7 20.8 25.6 41.5 25.6 17.4 0 28.6-8.7 28.6-20.8 0-14.4-11.4-19.5-30.7-28l-10.5-4.5c-30.4-12.9-50.5-29.2-50.5-63.5 0-31.6 24.1-55.6 61.6-55.6 26.8 0 46 9.3 59.8 33.7L368 290c-7.2-12.9-15-18-27.1-18-12.3 0-20.1 7.8-20.1 18 0 12.6 7.8 17.7 25.9 25.6l10.5 4.5c35.8 15.3 55.9 31 55.9 66.2 0 37.8-29.8 58.6-69.7 58.6z" />
    </svg>
  );
};

const SidebarSendData = ({ setOpen }: { setOpen: (open: boolean) => void }) => {
  return (
    <>
      <div className="flex flex-col col-span-1 justify-end">
        {/* <Button variant="link" className="flex" onClick={() => setOpen(false)}>
          Skip and continue later <ArrowRight className="h-4 w-4 ml-1" />
        </Button> */}
      </div>
    </>
  );
};

const APIKeyAndProjectId = () => {
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);

  if (!project_id) {
    return <></>;
  }

  return (
    <div className="flex items-center space-x-4">
      <Link
        href={`${process.env.NEXT_PUBLIC_AUTH_URL}/org/api_keys/${selectedOrgId}`}
        target="_blank"
      >
        <Button className="w-96">Create phospho API key</Button>
      </Link>

      <div className="flex items-center">
        <span className="w-32">Project id:</span>
        <Input value={project_id}></Input>
        <Button
          variant="outline"
          className="ml-2 p-3"
          size="icon"
          onClick={() => {
            navigator.clipboard.writeText(project_id);
          }}
        >
          <CopyIcon size="14" />
        </Button>
      </div>
    </div>
  );
};

export default function UploadDataset({
  setOpen,
  showModal,
  setShowModal,
  setButtonPressed,
}: {
  setOpen: (open: boolean) => void;
  showModal: boolean;
  setShowModal: (modal: boolean) => void;
  setButtonPressed: (buttonPressed: boolean) => void;
}) {
  const { toast } = useToast();
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const [loading] = React.useState(false);
  const [file, setFile] = React.useState<File | null>(null);

  const onSubmit = () => {
    if (showModal) {
      setShowModal(false);
      setButtonPressed(true);
    }
    if (!file) {
      toast({
        title: "Please select a file",
      });
      return;
    }
    console.log("onSubmit", file);
    const formData = new FormData();
    formData.set("file", file, file.name);
    try {
      // Call API to upload file
      fetch(`/api/projects/${project_id}/upload-tasks`, {
        method: "POST",
        headers: {
          Authorization: "Bearer " + accessToken,
          // "Content-Type": "multipart/form-data",
        },
        body: formData,
      }).then(async (response) => {
        if (response.ok) {
          toast({
            title: "Your file is being processed ✅",
            description:
              "Tasks will appear in your dashboard in a few minutes.",
          });
        } else {
          // Read the error details
          const error = await response.text();
          toast({
            title: "An error occurred",
            description: `${error}`,
          });
        }
      });
    } catch (error) {
      console.error("An unexpected error happened:", error);
      toast({
        title: "An error occurred",
        description: `${error}`,
      });
    }
  };

  return (
    <div className="flex flex-col space-y-2">
      <div className="text-sm mb-1">
        Upload a file with your historical data. The file should contain the
        following columns: <code>input</code>, <code>output</code>. Optionally,
        you can also include <code>session_id</code> and <code>created_at</code>{" "}
      </div>
      <u>
        <a href="/files/example_csv_phospho.csv" download="example_csv_phospho">
          Download example CSV
        </a>
      </u>
      <CopyBlock
        text={`input;output;task_id;session_id;created_at
"What's the capital of France?";"The capital of France is Paris";task_1;session_1;"2021-09-01 12:00:00"`}
        language={"text"}
        showLineNumbers={true}
        theme={dracula}
        wrapLongLines={true}
      />
      {/* <form className="w-full flex flex-col space-y-2"> */}
      <div className="flex flex-row space-x-2 items-center">
        <Plus className="w-4 h-4 mr-1" />
        <Input
          type="file"
          accept=".csv,.xlsx"
          placeholder="Pick file to upload"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              setFile(e.target.files[0]);
            }
          }}
        />
      </div>

      {/* {loading && (
            <div className="flex flex-row space-x-2 items-center justify-content">
              <div className="w-4 h-4 animate-spin">
                <LoaderCircle />
              </div>
            </div>
          )} */}
      {file !== null && (
        <Button onClick={onSubmit}>
          <Upload className="mr-1 w-4 h-4" />
          Confirm
        </Button>
      )}
      {/* </form> */}
    </div>
  );
}

const ToggleButton = ({ children }: { children: React.ReactNode }) => {
  return <div className="text-xl flex flex-row space-x-2">{children}</div>;
};

export const SendDataAlertDialog = ({
  setOpen,
}: {
  setOpen: (open: boolean) => void;
}) => {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const selectedOrgId = navigationStateStore((state) => state.selectedOrgId);
  const project_id = navigationStateStore((state) => state.project_id);
  const setproject_id = navigationStateStore((state) => state.setproject_id);
  const setSelectedOrgId = navigationStateStore(
    (state) => state.setSelectedOrgId,
  );
  const selectedOrgMetadata = dataStateStore(
    (state) => state.selectedOrgMetadata,
  );

  const [showModal, setShowModal] = React.useState(true);

  React.useEffect(() => {
    setShowModal(selectedOrgMetadata?.plan === "hobby");
  }, [selectedOrgMetadata?.plan]);

  //const [buttonPressed, setButtonPressed] = React.useState(false);
  const [buttonPressed, setButtonPressed] = React.useState(false);
  const delay = (ms: number) => new Promise((res) => setTimeout(res, ms));

  // NULL OR STR VALUE
  const [selectedTab, setSelectedTab] = React.useState<string | undefined>(
    undefined,
  );

  const { user, accessToken } = useUser();
  const toast = useToast();

  const formSchema = z.object({
    lang_smith_api_key: z
      .string()
      .min(50, {
        message: "Your API key should be longer than 50 characters.",
      })
      .max(60, {
        message: "Your API key should be shorter than 60 characters.",
      }),
    project_name: z
      .string()
      .min(2, {
        message: "Project name should be at least 2 characters.",
      })
      .max(32, {
        message: "Project name should be at most 30 characters.",
      }),
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    if (showModal) {
      setButtonPressed(true);
      setShowModal(false);
    }
    fetch(`/api/projects/${project_id}/connect-langsmith`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        project_name: values.project_name,
        langsmith_api_key: values.lang_smith_api_key,
      }),
    }).then(async (response) => {
      const responseBody = await response.json();
      if (response.ok) {
        toast.toast({
          title: "🦜🔗 LangSmith import successful",
          description: "Your data is being imported to phospho.",
        });
      } else {
        toast.toast({
          title: "🦜🔗 LangSmith import failed",
          description:
            "Please double-check your LangSmith API key and project name",
        });
      }
    });
  }

  async function createDefaultProject() {
    setOpen(false);
    if (!selectedOrgId) {
      // fetch the org id from the user
      const orgId = user?.getOrgs()[0].orgId;
      if (orgId) {
        setSelectedOrgId(orgId);
      } else {
        // if the user has no orgs, redirect to the auth
        router.push("/");
      }
    }
    //Create default project for orgID
    fetch(`/api/organizations/${selectedOrgId}/create-default-project`, {
      method: "POST",
      headers: {
        Authorization: "Bearer " + accessToken,
        "Content-Type": "application/json",
      },
    }).then(async (response) => {
      const responseBody = await response.json();
      if (responseBody.id !== undefined) {
        toast.toast({
          title: "We are creating your default project",
          description: "You will be redirected in a few seconds.",
        });
        await delay(1000);
        mutate([`/api/organizations/${selectedOrgId}/projects`, accessToken]);
        await delay(1000);
        setproject_id(responseBody.id);
        router.push(`/org`);
      } else {
        toast.toast({
          title: "Error when creating project",
          description: responseBody.error,
        });
      }
    });
  }

  function handleClose() {
    if (showModal) {
      setShowModal(false);
      setButtonPressed(true);
    } else {
      setOpen(false);
    }
  }

  function handleSkip() {
    setOpen(false);
    setButtonPressed(false);
    setShowModal(false);
  }

  if (!project_id) {
    return <></>;
  }

  return (
    <>
      {!buttonPressed && (
        <AlertDialogContent className="md:h-3/4 md:max-w-3/4">
          <AlertDialogHeader>
            <div className="flex justify-between">
              <div>
                <AlertDialogTitle className="text-2xl font-bold tracking-tight mb-1">
                  Start sending data to phospho
                </AlertDialogTitle>
                <AlertDialogDescription>
                  <p>
                    phospho detects events in the text data of your LLM app.
                  </p>
                </AlertDialogDescription>
              </div>
              <X onClick={handleClose} className="cursor-pointer h-8 w-8" />
            </div>
          </AlertDialogHeader>
          <div className="overflow-y-auto">
            <SidebarSendData setOpen={setOpen} />
            <div className="space-y-2 flex flex-col">
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl">
                    I need to log messages.
                  </CardTitle>
                  <CardDescription>
                    What's your app's backend language?
                  </CardDescription>
                  <ToggleGroup
                    type="single"
                    value={selectedTab}
                    onValueChange={(value) => setSelectedTab(value)}
                    className="justify-start"
                  >
                    <ToggleGroupItem value="python">
                      <ToggleButton>
                        <PythonIcon />
                        Python
                      </ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="javascript">
                      <ToggleButton>
                        <JavaScriptIcon />
                        JavaScript
                      </ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="api">
                      <ToggleButton>API</ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="other">
                      <ToggleButton>Other</ToggleButton>
                    </ToggleGroupItem>
                  </ToggleGroup>

                  {selectedTab == "python" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Use the following code snippets to log your app messages
                        to phospho.
                      </div>
                      <CopyBlock
                        text={`pip install --upgrade phospho`}
                        language={"shell"}
                        showLineNumbers={false}
                        theme={dracula}
                      />
                      <CopyBlock
                        text={`import phospho
              
phospho.init(api_key="YOUR_API_KEY", project_id="${project_id}")

input_str = "Hello! This is what the user asked to the system"
output_str = "This is the response showed to the user by the app."
phospho.log(input=input_str, output=output_str)`}
                        language={"python"}
                        showLineNumbers={false}
                        theme={dracula}
                        wrapLongLines={true}
                      />
                      <APIKeyAndProjectId />
                    </div>
                  )}
                  {selectedTab == "javascript" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Use the following code snippets to log your app messages
                        to phospho.
                      </div>
                      <CopyBlock
                        text={`npm i phospho`}
                        language={"shell"}
                        showLineNumbers={false}
                        theme={dracula}
                      />
                      <CopyBlock
                        text={`import { phospho } from "phospho";

phospho.init({apiKey: "YOUR_API_KEY", projectId: "${project_id}"});

const input = "Hello! This is what the user asked to the system";
const output = "This is the response showed to the user by the app.";
phospho.log({input, output});`}
                        language={"javascript"}
                        showLineNumbers={false}
                        theme={dracula}
                        wrapLongLines={true}
                      />
                      <APIKeyAndProjectId />
                    </div>
                  )}
                  {selectedTab == "api" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Use the following code snippets to log your app messages
                        to phospho.
                      </div>
                      <CopyBlock
                        text={`curl -X POST https://api.phospho.ai/v2/log/${project_id} \\
-H "Authorization: Bearer $PHOSPHO_API_KEY" \\
-H "Content-Type: application/json" \\
-d '{"batched_log_events": [
      {"input": "your_input", "output": "your_output"}
]}'`}
                        language={"bash"}
                        showLineNumbers={false}
                        theme={dracula}
                        wrapLongLines={true}
                      />
                      <APIKeyAndProjectId />
                    </div>
                  )}
                  {selectedTab == "other" && (
                    <div className="flex-col space-y-4">
                      <div className="flex space-x-2">
                        <Link
                          href="https://docs.phospho.ai/getting-started#how-to-setup-logging"
                          target="_blank"
                        >
                          <Button className="w-96">
                            Discover all integrations
                          </Button>
                        </Link>
                        <Link href="mailto:contact@phospho.app" target="_blank">
                          <Button variant="secondary">Contact us</Button>
                        </Link>
                      </div>
                    </div>
                  )}
                </CardHeader>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-xl">
                    I already store messages.
                  </CardTitle>
                  <CardDescription>
                    Push your historical data to phospho
                  </CardDescription>
                  <ToggleGroup
                    type="single"
                    value={selectedTab}
                    onValueChange={(value) => setSelectedTab(value)}
                    className="justify-start"
                  >
                    <ToggleGroupItem value="upload">
                      <ToggleButton>
                        <Upload className="mr-2 w-6 h-6" /> Upload dataset
                      </ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="lang_smith">
                      <ToggleButton>🦜🔗 LangSmith</ToggleButton>
                    </ToggleGroupItem>
                    <ToggleGroupItem value="other_bottom">
                      <ToggleButton>Other</ToggleButton>
                    </ToggleGroupItem>
                  </ToggleGroup>

                  {selectedTab == "upload" && (
                    <div className="flex-col space-y-4">
                      <UploadDataset
                        setOpen={setOpen}
                        showModal={showModal}
                        setShowModal={setShowModal}
                        setButtonPressed={setButtonPressed}
                      />
                    </div>
                  )}

                  {selectedTab == "lang_smith" && (
                    <div className="flex-col space-y-4">
                      <div className="text-sm">
                        Synchronise your data from LangSmith to phospho. We will
                        fetch the data periodically.
                      </div>
                      <Form {...form}>
                        <form
                          onSubmit={form.handleSubmit(onSubmit)}
                          className="space-y-8"
                        >
                          <FormField
                            control={form.control}
                            name="lang_smith_api_key"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>
                                  Your LangSmith API key,{" "}
                                  <Link
                                    className="underline hover:text-green-500"
                                    href="https://smith.langchain.com/o/b864875a-2a0c-537e-92f1-5df713478975/settings"
                                  >
                                    learn more here
                                  </Link>
                                </FormLabel>
                                <div className="flex justify-center">
                                  <HoverCard openDelay={80} closeDelay={30}>
                                    <HoverCardTrigger>
                                      <Lock className="mr-2 mt-2" />
                                    </HoverCardTrigger>
                                    <HoverCardContent
                                      side="top"
                                      className="text-sm text-center"
                                    >
                                      <div>
                                        This key is encrypted and stored
                                        securely.
                                      </div>
                                      <div>
                                        We only use it to fetch your data from
                                        LangSmith.
                                      </div>
                                    </HoverCardContent>
                                  </HoverCard>

                                  <FormControl>
                                    <PasswordInput
                                      placeholder="lsv2_..."
                                      {...field}
                                      className="font-normal flex"
                                    />
                                  </FormControl>
                                </div>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <FormField
                            control={form.control}
                            name="project_name"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>LangSmith project name</FormLabel>
                                <FormControl>
                                  <Input
                                    placeholder="My LangSmith project"
                                    {...field}
                                    className="font-normal"
                                  />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          <div className="flex justify-end">
                            <Button
                              type="submit"
                              disabled={!form.formState.isValid}
                            >
                              Transfer data from LangSmith
                            </Button>
                          </div>
                        </form>
                      </Form>
                    </div>
                  )}

                  {selectedTab == "other_bottom" && (
                    <div className="flex-col space-y-4">
                      <div className="flex space-x-2">
                        <Link
                          href="https://docs.phospho.ai/getting-started#how-to-setup-logging"
                          target="_blank"
                        >
                          <Button className="w-96">
                            Discover all integrations
                          </Button>
                        </Link>
                        <Link href="mailto:contact@phospho.app" target="_blank">
                          <Button variant="secondary">Contact us</Button>
                        </Link>
                      </div>
                    </div>
                  )}
                </CardHeader>
              </Card>
              <Alert>
                <AlertTitle className="text-sm">
                  I don't have an LLM app
                </AlertTitle>
                <AlertDescription className="flex flex-row items-center">
                  <Link href="https://www.youtube.com/watch?v=yQrRULUEiYM">
                    <Button variant="ghost" className="text-xs">
                      <MonitorPlay className="h-4 w-4 mr-2" />
                      Watch demo
                    </Button>
                  </Link>
                  <Link
                    href="https://colab.research.google.com/drive/1Wv9KHffpfHlQCxK1VGvP_ofnMiOGK83Q"
                    target="_blank"
                  >
                    <Button variant="ghost" className="text-xs">
                      <NotebookText className="h-4 w-4 mr-2" />
                      Example Colab notebook
                    </Button>
                  </Link>
                  <Button
                    variant="ghost"
                    className="text-xs"
                    onClick={() => createDefaultProject()}
                  >
                    <Telescope className="h-4 w-4 mr-2" />
                    Explore sample data
                  </Button>
                  <Button
                    variant="ghost"
                    className="text-xs"
                    onClick={() => router.push("mailto:paul-louis@phospho.app")}
                  >
                    <Mail className="h-4 w-4 mr-2" />
                    Contact us to create your own LLM app
                  </Button>
                </AlertDescription>
              </Alert>
            </div>
          </div>
        </AlertDialogContent>
      )}
      {buttonPressed && (
        <AlertDialogContent className=" md:max-w-1/2 flex flex-col justify-between">
          <AlertDialogHeader>
            <div className="flex justify-between">
              <div className="flex flex-col space-y-2 w-full">
                <AlertDialogTitle className="text-2xl font-bold tracking-tight mb-1">
                  One more thing...
                </AlertDialogTitle>
                <Card className="w-full border-red-500 bg-red-100">
                  <CardTitle className="text-xl mt-2 ml-2 text-black">
                    <div className="flex align-center">
                      <TriangleAlert className="mr-2" />
                      Your account is missing billing information
                    </div>
                  </CardTitle>
                  <CardHeader>
                    <CardDescription>
                      Please add payment information to enable data analytics
                    </CardDescription>
                  </CardHeader>
                </Card>
              </div>
            </div>
          </AlertDialogHeader>

          <div className="text-muted-foreground mx-[10%]">
            <p>
              By adding your information, you'll have access to advanced
              analytics features like:
            </p>
            <ul>
              <li> - Sentiment Analytics</li>
              <li> - Success/Failure flags</li>
              <li> - Custom event detection </li>
              <li> - Language Detection</li>
              <li> - Data Clustering</li>
            </ul>
          </div>

          <div className="flex justify-between">
            <Button onClick={() => handleSkip()} variant={"link"}>
              Ignore
            </Button>
            <UpgradeButton tagline="Enable Analytics" />
          </div>
        </AlertDialogContent>
      )}
    </>
  );
};

export const SendDataCallout = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  const [open, setOpen] = React.useState(false);

  return (
    <>
      {hasTasks === false && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex">
              <Unplug className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
              <div className="flex flex-grow justify-between items-center">
                <div>
                  <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                    Start sending data to phospho
                  </CardTitle>
                  <CardDescription className="flex justify-between">
                    We'll show you how to get started
                  </CardDescription>
                </div>
                <AlertDialog open={open}>
                  <Button
                    variant="default"
                    onClick={() => {
                      setOpen(true);
                    }}
                  >
                    Start sending data
                  </Button>
                  <SendDataAlertDialog setOpen={setOpen} />
                </AlertDialog>
              </div>
            </div>
          </CardHeader>
        </Card>
      )}
    </>
  );
};

export const DatavizCallout = () => {
  const { accessToken } = useUser();
  const project_id = navigationStateStore((state) => state.project_id);

  const { data: hasTasksData } = useSWR(
    project_id ? [`/api/explore/${project_id}/has-tasks`, accessToken] : null,
    ([url, accessToken]) => authFetcher(url, accessToken, "POST"),
    { keepPreviousData: true },
  );
  const hasTasks: boolean = hasTasksData?.has_tasks ?? false;

  const [open, setOpen] = React.useState(false);

  return (
    <>
      {hasTasks === false && (
        <Card className="bg-secondary">
          <CardHeader>
            <div className="flex">
              <BarChartBig className="mr-4 h-16 w-16 hover:text-green-500 transition-colors" />
              <div className="flex flex-grow justify-between items-center">
                <div>
                  <CardTitle className="text-2xl font-bold tracking-tight mb-0">
                    Visualize your augmented data
                  </CardTitle>
                  <CardDescription className="flex justify-between">
                    Quickly make plots and graphs with your data.
                  </CardDescription>
                </div>
                <AlertDialog open={open}>
                  <Button
                    variant="default"
                    onClick={() => {
                      setOpen(true);
                    }}
                  >
                    Start sending data
                  </Button>
                  <SendDataAlertDialog setOpen={setOpen} />
                </AlertDialog>
              </div>
            </div>
          </CardHeader>
        </Card>
      )}
    </>
  );
};
