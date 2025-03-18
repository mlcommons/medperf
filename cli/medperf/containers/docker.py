import docker


class DockerContainer:
    def __init__(self, container_file: str, image_hash: str = None):
        self.container_file = container_file
        self.image_hash = image_hash

    def download(self):
        url = self.image_tarball_url
        tarball_hash = self.image_tarball_hash

        if url:
            _, local_hash = resources.get_cube_image(url, self.path, tarball_hash)
            self.image_tarball_hash = local_hash
        else:
            if config.platform == "docker":
                # For docker, image should be pulled before calculating its hash
                self._get_image_from_registry()
                self._set_image_hash_from_registry()
            elif config.platform == "singularity":
                # For singularity, we need the hash first before trying to convert
                self._set_image_hash_from_registry()

                image_folder = os.path.join(config.cubes_folder, config.image_path)
                if os.path.exists(image_folder):
                    for file in os.listdir(image_folder):
                        if file == self._converted_singularity_image_name:
                            return
                        remove_path(os.path.join(image_folder, file))

                self._get_image_from_registry()
            else:
                # TODO: such a check should happen on commands entrypoints, not here
                raise InvalidArgumentError("Unsupported platform")

    def _set_image_hash_from_registry(self):
        # Retrieve image hash from MLCube
        logging.debug(f"Retrieving {self.id} image hash")
        tmp_out_yaml = generate_tmp_path()
        cmd = f"mlcube --log-level {config.loglevel} inspect --mlcube={self.cube_path} --format=yaml"
        cmd += f" --platform={config.platform} --output-file {tmp_out_yaml}"
        logging.info(f"Running MLCube command: {cmd}")
        with spawn_and_kill(cmd, timeout=config.mlcube_inspect_timeout) as proc_wrapper:
            proc = proc_wrapper.proc
            combine_proc_sp_text(proc)
        if proc.exitstatus != 0:
            raise ExecutionError("There was an error while inspecting the image hash")
        with open(tmp_out_yaml) as f:
            mlcube_details = yaml.safe_load(f)
        remove_path(tmp_out_yaml)
        local_hash = mlcube_details["hash"]
        if self.image_hash and local_hash != self.image_hash:
            raise InvalidEntityError(
                f"Hash mismatch. Expected {self.image_hash}, found {local_hash}."
            )
        self.image_hash = local_hash

    def _get_image_from_registry(self):
        # Retrieve image from image registry
        logging.debug(f"Retrieving {self.id} image")
        cmd = f"mlcube --log-level {config.loglevel} configure --mlcube={self.cube_path} --platform={config.platform}"
        if config.platform == "singularity":
            cmd += f" -Psingularity.image={self._converted_singularity_image_name}"
        logging.info(f"Running MLCube command: {cmd}")
        with spawn_and_kill(
            cmd, timeout=config.mlcube_configure_timeout
        ) as proc_wrapper:
            proc = proc_wrapper.proc
            combine_proc_sp_text(proc)
        if proc.exitstatus != 0:
            raise ExecutionError("There was an error while retrieving the MLCube image")

        """Executes a given task on the cube instance

        Args:
            task (str): task to run
            string_params (Dict[str], optional): Extra parameters that can't be passed as normal function args.
                                                 Defaults to {}.
            timeout (int, optional): timeout for the task in seconds. Defaults to None.
            read_protected_input (bool, optional): Wether to disable write permissions on input volumes. Defaults to True.
            kwargs (dict): additional arguments that are passed directly to the mlcube command
        """
        kwargs.update(string_params)
        cmd = f"mlcube --log-level {config.loglevel} run"
        cmd += f' --mlcube="{self.cube_path}" --task={task} --platform={config.platform} --network=none'
        if config.gpus is not None:
            cmd += f" --gpus={config.gpus}"
        if read_protected_input:
            cmd += " --mount=ro"
        for k, v in kwargs.items():
            cmd_arg = f'{k}="{v}"'
            cmd = " ".join([cmd, cmd_arg])

        container_loglevel = config.container_loglevel

        # TODO: we should override run args instead of what we are doing below
        #       we shouldn't allow arbitrary run args unless our client allows it
        if config.platform == "docker":
            # use current user
            cpu_args = self.get_config("docker.cpu_args") or ""
            gpu_args = self.get_config("docker.gpu_args") or ""
            cpu_args = " ".join([cpu_args, "-u $(id -u):$(id -g)"]).strip()
            gpu_args = " ".join([gpu_args, "-u $(id -u):$(id -g)"]).strip()
            cmd += f' -Pdocker.cpu_args="{cpu_args}"'
            cmd += f' -Pdocker.gpu_args="{gpu_args}"'

            if container_loglevel:
                cmd += f' -Pdocker.env_args="-e MEDPERF_LOGLEVEL={container_loglevel.upper()}"'
        elif config.platform == "singularity":
            # use -e to discard host env vars, -C to isolate the container (see singularity run --help)
            run_args = self.get_config("singularity.run_args") or ""
            run_args = " ".join([run_args, "-eC"]).strip()
            cmd += f' -Psingularity.run_args="{run_args}"'

            # set image name in case of running docker image with singularity
            # Assuming we only accept mlcube.yamls with either singularity or docker sections
            # TODO: make checks on submitted mlcubes
            singularity_config = self.get_config("singularity")
            if singularity_config is None:
                cmd += (
                    f' -Psingularity.image="{self._converted_singularity_image_name}"'
                )
            # TODO: pass logging env for singularity also there
        else:
            raise InvalidArgumentError("Unsupported platform")

        # set accelerator count to zero to avoid unexpected behaviours and
        # force mlcube to only use --gpus to figure out GPU config
        cmd += " -Pplatform.accelerator_count=0"

        logging.info(f"Running MLCube command: {cmd}")
        with spawn_and_kill(cmd, timeout=timeout) as proc_wrapper:
            proc = proc_wrapper.proc
            proc_out = combine_proc_sp_text(proc)

        if output_logs is not None:
            with open(output_logs, "w") as f:
                f.write(proc_out)
        if proc.exitstatus != 0:
            raise ExecutionError("There was an error while executing the cube")

        log_storage()
        return proc
