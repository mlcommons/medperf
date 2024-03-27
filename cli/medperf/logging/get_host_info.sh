
echo "#######################################"
echo "#           Machine Details           #"
echo "#######################################"
echo ""
echo "MEMORY USAGE:"
free
echo ""

echo "######################################"
echo "#            User Details            #"
echo "######################################"
echo ""
echo "USERNAME:"
whoami
echo ""
echo "USER GROUPS:"
groups
echo ""

echo "######################################"
echo "#           Docker Details           #"
echo "######################################"
echo ""
echo "DOCKER EXECUTABLE:"
echo "$(which docker 2>/dev/null || echo "not found")"
echo ""
echo "DOCKER INFORMATION:"
docker info
echo ""
echo "DOCKER VERSION:"
docker version
echo ""

echo "#######################################"
echo "#         Singularity Details         #"
echo "#######################################"
echo ""
echo "SINGULARITY EXECUTABLE:"
echo "$(which singularity 2>/dev/null || echo "not found")"
echo ""
echo "SINGULARITY CONFIGURATION:"
cat /usr/local/etc/singularity/singularity.conf
echo ""

echo "#######################################"
echo "#             GPU DETAILS             #"
echo "#######################################"
echo ""
echo "NVIDIA CONTAINER CLI EXECUTABLE:"
echo "$(which nvidia-container-cli 2>/dev/null || echo "not found")"
echo ""
echo "NVIDIA-SMI VERSION"
nvidia-smi --version
echo ""
echo "NVIDIA-SMI GPU-SPECIFIC-INFORMATION"
nvidia-smi --query-gpu=index,gpu_name,driver_version,compute_cap,memory.total
echo ""
echo "GPU(S) USAGE"
nvidia-smi
echo ""