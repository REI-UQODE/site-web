export function genererHash(str, longueur){
    let str_int = [];
    for(let i = 0; i < longueur; i++){
        str_int.push(str.charCodeAt(i % str.length));
    }
    for(let i = 1; i < Math.ceil(str.length/longueur); i++){
        for (let j = 0; j < longueur; j++){
            if (j + i*longueur < str.length){
                str_int[j] ^= str.charCodeAt((j + i*longueur)%str.length);
            }
        }
    }

    let ret = btoa(String.fromCharCode(...str_int));
    if(ret.length > longueur){
        ret = ret.substring(0, longueur);
    }
    return ret.replace('/','_').replace('+','-').replace('=','#');
}